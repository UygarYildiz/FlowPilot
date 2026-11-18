from email.message import EmailMessage

from flowpilot.core.ingestion.rfc822 import html_to_text, parse_rfc822


def _message() -> EmailMessage:
    message = EmailMessage()
    message["From"] = "Mert Özkan <Satis@OzkanRulman.example>"
    message["To"] = "Satın Alma <satinalma@atlas-endustri.example>, x@atlas-endustri.example"
    message["Cc"] = "kalite@atlas-endustri.example"
    message["Subject"] = "Fiyat teklifi — SAT-2026-031"
    message["Message-ID"] = "<abc123@ozkanrulman.example>"
    message["Date"] = "Wed, 18 Nov 2026 10:15:00 +0300"
    message.set_content("Teklifimiz ektedir.\nSaygılarımızla")
    message.add_alternative("<p>Teklifimiz <b>ektedir</b>.</p>", subtype="html")
    message.add_attachment(
        b"%PDF-1.4 ...", maintype="application", subtype="pdf", filename="teklif.pdf"
    )
    return message


def test_parses_headers_body_and_attachments() -> None:
    parsed = parse_rfc822(_message().as_bytes())
    assert parsed.message_id == "<abc123@ozkanrulman.example>"
    assert parsed.from_addr == "satis@ozkanrulman.example"
    assert parsed.to_addrs == ["satinalma@atlas-endustri.example", "x@atlas-endustri.example"]
    assert parsed.cc_addrs == ["kalite@atlas-endustri.example"]
    assert parsed.subject == "Fiyat teklifi — SAT-2026-031"
    assert parsed.body_text == "Teklifimiz ektedir.\nSaygılarımızla"
    assert parsed.received_at is not None and parsed.received_at.utcoffset() is not None
    assert [(a.filename, a.mime) for a in parsed.attachments] == [("teklif.pdf", "application/pdf")]
    assert parsed.attachments[0].content == b"%PDF-1.4 ..."


def test_html_only_body_is_converted_to_text() -> None:
    message = EmailMessage()
    message["From"] = "a@b.example"
    message["Subject"] = "Bilgi"
    message.set_content(
        "<div>Merhaba</div><script>x()</script><p>Sevkiyat yarın</p>", subtype="html"
    )
    parsed = parse_rfc822(message.as_bytes())
    assert parsed.body_text == "Merhaba\nSevkiyat yarın"
    assert parsed.message_id is None


def test_html_to_text_skips_style() -> None:
    assert html_to_text("<style>p{}</style><p>a</p><br>b") == "a\nb"
