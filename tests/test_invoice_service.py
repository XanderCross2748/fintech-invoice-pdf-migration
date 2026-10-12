import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from invoice_service import Order, generate_invoice


class FakePdf:
    def __init__(self):
        self.calls = []

    def generate(self, html, request_id):
        self.calls.append((html, request_id))
        return {"url": "signed-pdf-result"}


def test_unpaid_order_is_held_without_pdf_call():
    client = FakePdf()
    result = generate_invoice(Order("ord-7", "Ada", "USD", 1250, False), client)
    assert result == {"status": "held", "reason": "payment_pending", "order_id": "ord-7"}
    assert client.calls == []


def test_paid_order_is_issued_with_invoice_content():
    client = FakePdf()
    result = generate_invoice(Order("ord-8", "Ada", "USD", 1250, True), client)
    assert result["status"] == "issued"
    assert "Invoice ord-8" in client.calls[0][0]
    assert client.calls[0][1]
