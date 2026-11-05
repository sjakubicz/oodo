from decimal import Decimal

import httpx
from celery import shared_task
from celery.contrib.django.task import DjangoTask

from .ksef import KsefRejectedError, KsefUnavailableError, submit_invoice
from .models import Invoice
from .odoo import odoo_client


class RetryingTask(DjangoTask):
    acks_late = True
    max_retries = 8
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = True


@shared_task
def pull_posted_invoices() -> None:
    for move in odoo_client().posted_invoices_without_ksef_number():
        invoice, created = Invoice.objects.get_or_create(
            odoo_id=move["id"],
            defaults={
                "number": move["name"],
                "amount_total": Decimal(str(move["amount_total"])).quantize(Decimal("0.01")),
                "currency": move["currency_id"][1],
            },
        )
        if created:
            send_to_ksef.delay_on_commit(invoice.pk)


@shared_task(base=RetryingTask, autoretry_for=(KsefUnavailableError, httpx.TransportError))
def send_to_ksef(invoice_id: int) -> None:
    invoice = Invoice.objects.get(pk=invoice_id)
    if invoice.status != Invoice.Status.PENDING:
        return
    try:
        invoice.ksef_number = submit_invoice(invoice)
    except KsefRejectedError as rejection:
        invoice.status = Invoice.Status.REJECTED
        invoice.rejection_reason = str(rejection)
        invoice.save(update_fields=["status", "rejection_reason", "updated_at"])
        return
    invoice.status = Invoice.Status.SENT
    invoice.save(update_fields=["status", "ksef_number", "updated_at"])
    write_ksef_number_to_odoo.delay(invoice.pk)


@shared_task(base=RetryingTask, autoretry_for=(OSError,))
def write_ksef_number_to_odoo(invoice_id: int) -> None:
    invoice = Invoice.objects.get(pk=invoice_id)
    if invoice.status != Invoice.Status.SENT:
        return
    odoo_client().set_ksef_number(invoice.odoo_id, invoice.ksef_number)
    invoice.status = Invoice.Status.SYNCED
    invoice.save(update_fields=["status", "updated_at"])
