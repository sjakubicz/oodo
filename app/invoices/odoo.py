import xmlrpc.client
from typing import Any

from django.conf import settings


class OdooClient:
    def __init__(self, url: str, db: str, login: str, password: str) -> None:
        self.db = db
        self.password = password
        self.uid = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common").authenticate(db, login, password, {})
        self.models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    def call(self, model: str, method: str, *args: Any, **kwargs: Any) -> Any:
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, list(args), kwargs)

    def posted_invoices_without_ksef_number(self) -> list[dict[str, Any]]:
        return self.call(
            "account.move",
            "search_read",
            [("move_type", "=", "out_invoice"), ("state", "=", "posted"), ("ksef_number", "=", False)],
            fields=["name", "amount_total", "currency_id"],
        )

    def set_ksef_number(self, move_id: int, ksef_number: str) -> None:
        self.call("account.move", "write", [move_id], {"ksef_number": ksef_number})


def odoo_client() -> OdooClient:
    return OdooClient(settings.ODOO_URL, settings.ODOO_DB, settings.ODOO_LOGIN, settings.ODOO_PASSWORD)
