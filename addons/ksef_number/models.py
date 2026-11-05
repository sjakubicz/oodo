from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    ksef_number = fields.Char(string="KSeF Number", copy=False, index=True, readonly=True)
    is_overdue = fields.Boolean(string="Overdue", compute="_compute_is_overdue")

    @api.depends("invoice_date_due", "payment_state", "state")
    def _compute_is_overdue(self):
        today = fields.Date.context_today(self)
        for move in self:
            move.is_overdue = bool(
                move.is_invoice()
                and move.state == "posted"
                and move.invoice_date_due
                and move.invoice_date_due < today
                and move.payment_state not in ("paid", "in_payment", "reversed")
            )
