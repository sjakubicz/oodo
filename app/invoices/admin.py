from django.contrib import admin

from .models import Invoice


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "amount_total", "currency", "status", "ksef_number", "updated_at")
    list_filter = ("status",)
    search_fields = ("number", "ksef_number")
