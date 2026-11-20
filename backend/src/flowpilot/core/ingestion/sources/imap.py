"""IMAP adaptörü (ADR-007): gerçek bir posta kutusunu salt-okunur okur.

Posta kutusunda hiçbir şeyi değiştirmez (okundu işareti dahil). Son `since_days` günün
e-postalarını getirir; daha önce kaydedilenleri giriş servisinin tekrar önlemesi ayıklar.
"""

import contextlib
import imaplib
from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta
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
