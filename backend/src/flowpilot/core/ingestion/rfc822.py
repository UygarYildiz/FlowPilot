"""Ham e-postayı (RFC 822 / .eml) `IncomingEmail`'e çevirir. IMAP adaptörü bunu kullanır."""

from email import message_from_bytes, policy
from email.message import EmailMessage
from email.utils import getaddresses, parseaddr, parsedate_to_datetime
from html.parser import HTMLParser

from flowpilot.core.ingestion.types import IncomingAttachment, IncomingEmail


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip += 1
        elif tag in ("br", "p", "div", "tr", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self.parts.append(data)


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    lines = (line.strip() for line in "".join(parser.parts).splitlines())
    return "\n".join(line for line in lines if line)


def _addresses(message: EmailMessage, header: str) -> list[str]:
    values = message.get_all(header, [])
    return [addr.lower() for _, addr in getaddresses([str(v) for v in values]) if addr]


def parse_rfc822(raw: bytes) -> IncomingEmail:
    message = message_from_bytes(raw, policy=policy.default)
    if not isinstance(message, EmailMessage):
        raise TypeError("Beklenmeyen e-posta nesnesi")

    body = ""
    part = message.get_body(preferencelist=("plain", "html"))
    if isinstance(part, EmailMessage):
        content = part.get_content()
        body = html_to_text(content) if part.get_content_type() == "text/html" else content

    attachments = []
    for index, attachment in enumerate(message.iter_attachments()):
        payload = attachment.get_payload(decode=True)
        if not isinstance(payload, bytes):
            continue
        attachments.append(
            IncomingAttachment(
                filename=attachment.get_filename() or f"ek-{index + 1}",
                mime=attachment.get_content_type(),
                content=payload,
            )
        )

    received_at = None
    if date := message.get("Date"):
        try:
            received_at = parsedate_to_datetime(str(date))
        except (TypeError, ValueError):
            received_at = None

    return IncomingEmail(
        message_id=str(message.get("Message-ID") or "").strip() or None,
        from_addr=parseaddr(str(message.get("From", "")))[1].lower(),
        to_addrs=_addresses(message, "To"),
        cc_addrs=_addresses(message, "Cc"),
        subject=str(message.get("Subject", "")),
        body_text=body.strip(),
        received_at=received_at,
        attachments=attachments,
    )
