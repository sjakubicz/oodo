import os
import random
import uuid
from datetime import date
from decimal import Decimal

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

FAILURE_RATE = float(os.environ.get("FAILURE_RATE", "0.3"))

app = FastAPI(title="KSeF mock")
ksef_numbers_by_idempotency_key: dict[str, str] = {}


class InvoiceIn(BaseModel):
    number: str = Field(min_length=1)
    amount_total: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)


class InvoiceAccepted(BaseModel):
    ksef_number: str


@app.post("/invoices", status_code=201)
def submit_invoice(invoice: InvoiceIn, idempotency_key: str = Header()) -> InvoiceAccepted:
    if idempotency_key in ksef_numbers_by_idempotency_key:
        return InvoiceAccepted(ksef_number=ksef_numbers_by_idempotency_key[idempotency_key])
    if random.random() < FAILURE_RATE:
        raise HTTPException(status_code=503, detail="KSeF temporarily unavailable")
    ksef_number = f"{date.today():%Y%m%d}-{uuid.uuid4().hex[:12].upper()}"
    ksef_numbers_by_idempotency_key[idempotency_key] = ksef_number
    return InvoiceAccepted(ksef_number=ksef_number)
