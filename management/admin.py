from django.contrib import admin
from django.db.models import Sum, F
from django.utils.html import format_html
from .models import (
    Supplier,
    Buyer,
    ProductType,
    Purchase,
    Sale,
    Payment,
    InventoryLoss
)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'total_purchases', 'total_outstanding')
    search_fields = ('name', 'phone')
    list_per_page = 20

    def total_purchases(self, obj):
        total = Purchase.objects.filter(supplier=obj).aggregate(
            total=Sum(F('bought_kgs') * F('price_per_kg')))['total']
        return f"₹{total or 0:,.2f}"

    def total_outstanding(self, obj):
        purchases_total = Purchase.objects.filter(supplier=obj).aggregate(
            total=Sum(F('bought_kgs') * F('price_per_kg')))['total'] or 0
        payments_total = Payment.objects.filter(
            purchase__supplier=obj,
            payment_type='PURCHASE'
        ).aggregate(total=Sum('amount'))['total'] or 0
        outstanding = purchases_total - payments_total
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            'red' if outstanding > 0 else 'green',
            outstanding
        )


@admin.register(Buyer)
class BuyerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'total_purchases', 'total_outstanding')
    search_fields = ('name', 'phone')
    list_per_page = 20

    def total_purchases(self, obj):
        total = Sale.objects.filter(buyer=obj).aggregate(
            total=Sum(F('quantity_kgs') * F('price_per_kg')))['total']
        return f"₹{total or 0:,.2f}"

    def total_outstanding(self, obj):
        sales_total = Sale.objects.filter(buyer=obj).aggregate(
            total=Sum(F('quantity_kgs') * F('price_per_kg')))['total'] or 0
        payments_total = Payment.objects.filter(
            sale__buyer=obj,
            payment_type='SALE'
        ).aggregate(total=Sum('amount'))['total'] or 0
        outstanding = sales_total - payments_total
        return format_html(
            '<span style="color: {};">₹{:,.2f}</span>',
            'red' if outstanding > 0 else 'green',
            outstanding
        )


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'total_inventory')
    search_fields = ('name',)

    def total_inventory(self, obj):
        purchases = Purchase.objects.filter(product_type=obj).aggregate(
            total=Sum('bought_kgs'))['total'] or 0
        sales = Sale.objects.filter(purchase__product_type=obj).aggregate(
            total=Sum('quantity_kgs'))['total'] or 0
        losses = InventoryLoss.objects.filter(purchase__product_type=obj).aggregate(
            total=Sum('quantity_kgs'))['total'] or 0
        return f"{purchases - (sales or 0) - (losses or 0):,.2f} kg"


class SaleInline(admin.TabularInline):
    model = Sale
    extra = 0
    readonly_fields = ('total_amount',)


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    fields = ('date', 'amount', 'notes')


class InventoryLossInline(admin.TabularInline):
    model = InventoryLoss
    extra = 0


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('date', 'supplier', 'product_type', 'bought_kgs',
                    'remaining_kgs', 'total_amount', 'payment_status')
    list_filter = ('supplier', 'product_type', 'date')
    search_fields = ('supplier__name', 'product_type__name')
    date_hierarchy = 'date'
    inlines = [SaleInline, PaymentInline, InventoryLossInline]
    readonly_fields = ('total_amount', 'remaining_kgs')
    list_per_page = 20

    def payment_status(self, obj):
        total = obj.total_amount
        paid = obj.payments.aggregate(total=Sum('amount'))['total'] or 0
        status = paid / total * 100 if total else 0
        color = 'green' if status >= 100 else 'orange' if status >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}% Paid</span>',
            color,
            status
        )


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('date', 'buyer', 'purchase', 'quantity_kgs',
                    'price_per_kg', 'total_amount', 'payment_status')
    list_filter = ('buyer', 'purchase__product_type', 'date')
    search_fields = ('buyer__name', 'purchase__supplier__name')
    date_hierarchy = 'date'
    inlines = [PaymentInline]
    readonly_fields = ('total_amount',)
    list_per_page = 20

    def payment_status(self, obj):
        total = obj.total_amount
        paid = obj.payments.aggregate(total=Sum('amount'))['total'] or 0
        status = paid / total * 100 if total else 0
        color = 'green' if status >= 100 else 'orange' if status >= 50 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}% Paid</span>',
            color,
            status
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('date', 'payment_type', 'related_entity', 'amount')
    list_filter = ('payment_type', 'date')
    search_fields = ('purchase__supplier__name', 'sale__buyer__name')
    date_hierarchy = 'date'
    list_per_page = 20

    def related_entity(self, obj):
        if obj.payment_type == 'PURCHASE':
            return f"Purchase - {obj.purchase.supplier.name}"
        return f"Sale - {obj.sale.buyer.name}"


@admin.register(InventoryLoss)
class InventoryLossAdmin(admin.ModelAdmin):
    list_display = ('date', 'purchase', 'quantity_kgs', 'reason')
    list_filter = ('purchase__product_type', 'date')
    search_fields = ('purchase__supplier__name', 'reason')
    date_hierarchy = 'date'
    list_per_page = 20
