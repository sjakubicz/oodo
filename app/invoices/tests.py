from decimal import Decimal
from unittest.mock import patch

import pytest

from .ksef import KsefRejectedError, KsefUnavailableError
from .models import Invoice
from .tasks import pull_posted_invoices, send_to_ksef, write_ksef_number_to_odoo

pytestmark = pytest.mark.django_db

ODOO_MOVE = {"id": 7, "name": "INV/2026/00007", "amount_total": 1230.0, "currency_id": [1, "PLN"]}


@pytest.fixture
def pending_invoice():
    return Invoice.objects.create(odoo_id=7, number="INV/2026/00007", amount_total=Decimal("1230.00"), currency="PLN")


@patch.object(send_to_ksef, "delay_on_commit")
@patch("invoices.tasks.odoo_client")
def test_pull_creates_each_invoice_once(odoo_client, delay_on_commit):
    odoo_client.return_value.posted_invoices_without_ksef_number.return_value = [ODOO_MOVE]

    pull_posted_invoices()
    pull_posted_invoices()

    invoice = Invoice.objects.get()
    assert invoice.amount_total == Decimal("1230.00")
    assert invoice.currency == "PLN"
    delay_on_commit.assert_called_once_with(invoice.pk)


@patch.object(write_ksef_number_to_odoo, "delay")
@patch("invoices.tasks.submit_invoice", return_value="20261105-ABC")
def test_send_stores_ksef_number_and_schedules_write_back(submit_invoice, write_back, pending_invoice):
    send_to_ksef(pending_invoice.pk)

    pending_invoice.refresh_from_db()
    assert pending_invoice.status == Invoice.Status.SENT
    assert pending_invoice.ksef_number == "20261105-ABC"
    write_back.assert_called_once_with(pending_invoice.pk)


@patch("invoices.tasks.submit_invoice")
def test_send_skips_already_sent_invoice(submit_invoice, pending_invoice):
    pending_invoice.status = Invoice.Status.SENT
    pending_invoice.save()

    send_to_ksef(pending_invoice.pk)

    submit_invoice.assert_not_called()


@patch("invoices.tasks.submit_invoice", side_effect=KsefRejectedError("amount_total must be > 0"))
def test_send_stores_rejection_reason(submit_invoice, pending_invoice):
    send_to_ksef(pending_invoice.pk)

    pending_invoice.refresh_from_db()
    assert pending_invoice.status == Invoice.Status.REJECTED
    assert "amount_total" in pending_invoice.rejection_reason


@patch("invoices.tasks.submit_invoice", side_effect=KsefUnavailableError("503"))
def test_send_keeps_invoice_pending_when_ksef_is_down(submit_invoice, pending_invoice):
    with pytest.raises(KsefUnavailableError):
        send_to_ksef(pending_invoice.pk)

    pending_invoice.refresh_from_db()
    assert pending_invoice.status == Invoice.Status.PENDING


@patch("invoices.tasks.odoo_client")
def test_write_back_marks_invoice_synced(odoo_client, pending_invoice):
    pending_invoice.status = Invoice.Status.SENT
    pending_invoice.ksef_number = "20261105-ABC"
    pending_invoice.save()

    write_ksef_number_to_odoo(pending_invoice.pk)

    odoo_client.return_value.set_ksef_number.assert_called_once_with(7, "20261105-ABC")
    pending_invoice.refresh_from_db()
    assert pending_invoice.status == Invoice.Status.SYNCED
