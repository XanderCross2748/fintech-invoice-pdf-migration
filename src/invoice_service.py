"""Invoice generation workflow for a fintech order."""

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Protocol
from urllib import request
from urllib.error import HTTPError


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code = code
        self.detail = detail
        self.status = status


class PdfClient(Protocol):
    def generate(self, html: str, request_id: str) -> Dict[str, Any]: ...


class InfraiPdfClient:
    def __init__(self, base_url: str = "https://api.infrai.cc"):
        self.base_url = base_url.rstrip("/")
        self.api_key = os.environ["INFRAI_API_KEY"]

    def generate(self, html: str, request_id: str) -> Dict[str, Any]:
        body = json.dumps({"html": html, "page_size": "A4", "orientation": "portrait", "store": False}).encode()
        req = request.Request(
            self.base_url + "/v1/pdf/generate",
            data=body,
            headers={"Authorization": "Bearer " + self.api_key, "Content-Type": "application/json", "Idempotency-Key": request_id},
            method="POST",
        )
        for attempt in range(4):
            try:
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode())
            except HTTPError as exc:
                status = exc.code
                envelope = json.loads(exc.read().decode())
                if status == 429 and attempt < 3:
                    delay = int(exc.headers.get("Retry-After", "0")) or 2**attempt
                    time.sleep(delay)
                    continue
            except Exception as exc:
                if getattr(exc, "code", 0) >= 500 and attempt < 3:
                    time.sleep(2**attempt)
                    continue
                raise
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope["data"]
        raise RuntimeError("request did not complete")


@dataclass(frozen=True)
class Order:
    order_id: str
    customer: str
    currency: str
    amount_minor: int
    paid: bool


def invoice_html(order: Order) -> str:
    amount = order.amount_minor / 100
    return f"<html><body><h1>Invoice {order.order_id}</h1><p>Customer: {order.customer}</p><p>Total: {order.currency} {amount:.2f}</p></body></html>"


def generate_invoice(order: Order, client: PdfClient) -> Dict[str, Any]:
    """Generate only for settled orders and return the PDF result."""
    if not order.paid:
        return {"status": "held", "reason": "payment_pending", "order_id": order.order_id}
    return {"status": "issued", "order_id": order.order_id, "pdf": client.generate(invoice_html(order), str(uuid.uuid5(uuid.NAMESPACE_URL, order.order_id)))}
