"""IMAP adaptörü (ADR-007): gerçek bir posta kutusunu salt-okunur okur.

Posta kutusunda hiçbir şeyi değiştirmez (okundu işareti dahil). Son `since_days` günün
e-postalarını getirir; daha önce kaydedilenleri giriş servisinin tekrar önlemesi ayıklar.
"""

import contextlib
import imaplib
import select
import time
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
from email.parser import BytesHeaderParser
from typing import Any

from flowpilot.core.ingestion.rfc822 import parse_rfc822
from flowpilot.core.ingestion.types import IncomingEmail

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def imap_date(value: datetime) -> str:
    """IMAP SEARCH için tarih (ör. 18-Nov-2026); yerel ayardan bağımsız."""
    return f"{value.day:02d}-{_MONTHS[value.month - 1]}-{value.year}"


class ImapError(Exception):
    pass


class ImapSource:
    name = "imap"

    def __init__(
        self,
        *,
        host: str,
        user: str,
        password: str,
        port: int = 993,
        folder: str = "INBOX",
        since_days: int = 7,
        connect: Callable[[str, int], Any] | None = None,
        now: datetime | None = None,
    ) -> None:
        self._host, self._port = host, port
        self._user, self._password = user, password
        self._folder = folder
        self._since_days = since_days
        self._connect = connect or imaplib.IMAP4_SSL
        self._now = now or datetime.now(UTC)

    @staticmethod
    def _check(result: tuple[str, Any], what: str) -> Any:
        status, data = result
        if status != "OK":
            raise ImapError(f"IMAP {what} başarısız: {data!r}")
        return data

    def fetch(self) -> Iterator[IncomingEmail]:
        conn = self._connect(self._host, self._port)
        try:
            self._check(conn.login(self._user, self._password), "LOGIN")
            self._check(conn.select(self._folder, readonly=True), "SELECT")
            since = imap_date(self._now - timedelta(days=self._since_days))
            data = self._check(conn.uid("SEARCH", "SINCE", since), "SEARCH")
            uids = data[0].split() if data and data[0] else []
            for uid in uids:
                # BODY.PEEK[] e-postayı okundu olarak işaretlemez.
                parts = self._check(conn.uid("FETCH", uid, "(BODY.PEEK[])"), "FETCH")
                raw = next((p[1] for p in parts if isinstance(p, tuple)), None)
                if isinstance(raw, bytes):
                    yield parse_rfc822(raw)
        finally:
            with contextlib.suppress(Exception):
                conn.logout()


def _uid_list(data: Any) -> list[int]:
    return sorted(int(u) for u in (data[0].split() if data and data[0] else []))


def _payload(parts: Any) -> bytes | None:
    return next((p[1] for p in parts if isinstance(p, tuple) and isinstance(p[1], bytes)), None)


def _select_readable(sock: Any, timeout: float) -> bool:
    """Bağlantıda okunacak veri olana dek bekler (en çok `timeout` sn)."""
    pending = getattr(sock, "pending", None)
    if callable(pending) and pending():
        return True
    readable, _, _ = select.select([sock], [], [], timeout)
    return bool(readable)


class ImapMailbox:
    """Sürekli açık IMAP bağlantısı (ADR-017): yeni e-postaları getirir, gelişlerini bekler.

    Salt-okunur (`readonly` SELECT, `BODY.PEEK`): posta kutusunda hiçbir şey değişmez.
    İlk çağrıda son `since_days` günü tarar; daha önce kaydedilmiş e-postaları (`is_known`)
    yalnızca başlığını indirerek atlar. Sonra yalnızca son görülen UID'den büyükleri getirir.
    Sunucu IDLE destekliyorsa `wait` yeni e-posta gelince hemen döner; yoksa bekleyip yoklar.
    """

    name = "imap"

    def __init__(
        self,
        *,
        host: str,
        user: str,
        password: str,
        port: int = 993,
        folder: str = "INBOX",
        since_days: int = 7,
        is_known: Callable[[str], bool] = lambda message_id: False,
        connect: Callable[[str, int], Any] | None = None,
        readable: Callable[[Any, float], bool] = _select_readable,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._host, self._port = host, port
        self._user, self._password = user, password
        self._folder = folder
        self._since_days = since_days
        self._is_known = is_known
        self._connect = connect or imaplib.IMAP4_SSL
        self._readable = readable
        self._now = now
        self._conn: Any = None
        self._uidvalidity: bytes | None = None
        self.last_uid: int | None = None

    @property
    def is_open(self) -> bool:
        return self._conn is not None

    @property
    def supports_idle(self) -> bool:
        caps = getattr(self._conn, "capabilities", ()) or ()
        return "IDLE" in {str(c).upper() for c in caps}

    def open(self) -> None:
        conn = self._connect(self._host, self._port)
        self._conn = conn
        try:
            ImapSource._check(conn.login(self._user, self._password), "LOGIN")
            ImapSource._check(conn.select(self._folder, readonly=True), "SELECT")
        except Exception:
            self.close()
            raise
        _, data = conn.response("UIDVALIDITY")
        uidvalidity = data[0] if data and data[0] else None
        if uidvalidity != self._uidvalidity:
            # Posta kutusu yeniden numaralandı (ya da ilk bağlantı): baştan tara.
            self._uidvalidity, self.last_uid = uidvalidity, None

    def close(self) -> None:
        conn, self._conn = self._conn, None
        if conn is not None:
            with contextlib.suppress(Exception):
                conn.logout()

    def fetch(self) -> Iterator[IncomingEmail]:
        """Yeni e-postalar (EmailSource). Bağlantı kapalıysa açar."""
        if self._conn is None:
            self.open()
        conn: Any = self._conn
        last_uid = self.last_uid
        initial = last_uid is None
        if last_uid is None:
            since = imap_date(self._now() - timedelta(days=self._since_days))
            uids = _uid_list(ImapSource._check(conn.uid("SEARCH", "SINCE", since), "SEARCH"))
        else:
            criteria = f"{last_uid + 1}:*"
            found = ImapSource._check(conn.uid("SEARCH", "UID", criteria), "SEARCH")
            # "n:*" kutudaki son e-postayı her zaman döndürür; gerçekten yeni olanları tut.
            uids = [u for u in _uid_list(found) if u > last_uid]
        if initial and not uids:
            self.last_uid = 0
        for uid in uids:
            key = str(uid).encode()
            if initial and self._already_known(conn, key):
                self.last_uid = uid
                continue
            parts = ImapSource._check(conn.uid("FETCH", key, "(BODY.PEEK[])"), "FETCH")
            raw = _payload(parts)
            self.last_uid = uid
            if raw is not None:
                yield parse_rfc822(raw)

    def _already_known(self, conn: Any, key: bytes) -> bool:
        spec = "(BODY.PEEK[HEADER.FIELDS (MESSAGE-ID)])"
        header = _payload(ImapSource._check(conn.uid("FETCH", key, spec), "FETCH"))
        if not header:
            return False
        message_id = str(BytesHeaderParser().parsebytes(header).get("Message-ID") or "").strip()
        return bool(message_id) and self._is_known(message_id)

    def wait(self, timeout: float, *, poll_seconds: float = 60.0) -> bool:
        """Yeni e-posta gelene ya da süre dolana dek bekler. Sunucu haber verdiyse True."""
        if self._conn is None:
            raise ImapError("Bağlantı kapalı")
        if not self.supports_idle:
            time.sleep(min(timeout, poll_seconds))
            return False
        return self._idle(timeout)

    def _idle(self, timeout: float) -> bool:
        """RFC 2177 IDLE: sunucu `* n EXISTS` gönderene ya da süre dolana dek bekler."""
        conn = self._conn
        tag = conn._new_tag()
        conn.send(tag + b" IDLE\r\n")
        line = conn.readline()
        if not line.startswith(b"+"):
            raise ImapError(f"IMAP IDLE reddedildi: {line!r}")
        signalled = False
        deadline = time.monotonic() + timeout
        try:
            while (left := deadline - time.monotonic()) > 0:
                if not self._readable(conn.sock, left):
                    break
                line = conn.readline()
                if not line:
                    raise ImapError("IMAP bağlantısı kapandı")
                if b"EXISTS" in line.upper():
                    signalled = True
                    break
        finally:
            conn.send(b"DONE\r\n")
            while True:
                line = conn.readline()
                if not line:
                    raise ImapError("IMAP bağlantısı kapandı")
                if line.startswith(tag):
                    if not line[len(tag) :].strip().upper().startswith(b"OK"):
                        raise ImapError(f"IMAP IDLE bitmedi: {line!r}")
                    break
        return signalled
