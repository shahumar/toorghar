from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Supplier(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Buyer(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class ProductType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Purchase(models.Model):
    date = models.DateField()
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    product_type = models.ForeignKey(ProductType, on_delete=models.PROTECT)

    bought_kgs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    # Costs
    labour_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    transportation_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    trip_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    maintenance_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        if self.bought_kgs and self.price_per_kg and self.total_costs:
            return self.bought_kgs * self.price_per_kg + self.total_costs
        0

    @property
    def total_costs(self):
        return (
                self.labour_cost +
                self.transportation_cost +
                self.trip_cost +
                self.maintenance_cost
        )

    @property
    def remaining_kgs(self):
        sold_kgs = sum(sale.quantity_kgs for sale in self.sales.all())
        lost_kgs = sum(loss.quantity_kgs for loss in self.losses.all())
        if self.bought_kgs and sold_kgs and lost_kgs:
            return self.bought_kgs - sold_kgs - lost_kgs
        0

    def __str__(self):
        return f"{self.date} - {self.supplier.name} - {self.bought_kgs}kg"


class Sale(models.Model):
    date = models.DateField()
    purchase = models.ForeignKey(Purchase, related_name='sales', on_delete=models.PROTECT)
    buyer = models.ForeignKey(Buyer, on_delete=models.PROTECT)

    quantity_kgs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_amount(self):
        if self.quantity_kgs and self.price_per_kg:
            return self.quantity_kgs * self.price_per_kg
        0

    def __str__(self):
        return f"{self.date} - {self.buyer.name} - {self.quantity_kgs}kg"


class Payment(models.Model):
    PAYMENT_TYPE_CHOICES = [
        ('PURCHASE', 'Purchase Payment'),
        ('SALE', 'Sale Payment'),
    ]

    date = models.DateField()
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES)
    purchase = models.ForeignKey(Purchase, null=True, blank=True, related_name='payments', on_delete=models.PROTECT)
    sale = models.ForeignKey(Sale, null=True, blank=True, related_name='payments', on_delete=models.PROTECT)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        related_to = self.purchase if self.payment_type == 'PURCHASE' else self.sale
        return f"{self.date} - {self.amount} - {related_to}"


class InventoryLoss(models.Model):
    date = models.DateField()
    purchase = models.ForeignKey(Purchase, related_name='losses', on_delete=models.PROTECT)
    quantity_kgs = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.date} - Loss {self.quantity_kgs}kg"