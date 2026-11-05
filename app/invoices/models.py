from django.db import models


class Invoice(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending"
        SENT = "sent"
        SYNCED = "synced"
        REJECTED = "rejected"

    odoo_id = models.PositiveIntegerField(unique=True)
    number = models.CharField(max_length=64)
    amount_total = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=16, choices=Status, default=Status.PENDING)
    ksef_number = models.CharField(max_length=64, blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.number
