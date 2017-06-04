from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem, Supplier, ImportOrder, ImportOrderItem, PaymentHistory


class PuchaserOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    raw_id_fields = ['order']


class ImportOrderItemInline(admin.TabularInline):
    model = ImportOrderItem
    raw_id_fields = ['order']


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['order', 'total_count']
    inlines = [PuchaserOrderItemInline]


@admin.register(ImportOrder)
class ImportOrderAdmin(admin.ModelAdmin):
    inlines = [ImportOrderItemInline]


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    pass


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    pass
