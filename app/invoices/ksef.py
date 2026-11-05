import httpx
from django.conf import settings

from .models import Invoice


class KsefUnavailableError(Exception):
    pass


class KsefRejectedError(Exception):
    pass


def submit_invoice(invoice: Invoice) -> str:
    response = httpx.post(
        f"{settings.KSEF_URL}/invoices",
        json={"number": invoice.number, "amount_total": str(invoice.amount_total), "currency": invoice.currency},
        headers={"Idempotency-Key": f"odoo-move-{invoice.odoo_id}"},
        timeout=10,
    )
    if response.is_server_error:
        raise KsefUnavailableError(response.text)
    if response.is_client_error:
        raise KsefRejectedError(response.text)
    return response.json()["ksef_number"]
