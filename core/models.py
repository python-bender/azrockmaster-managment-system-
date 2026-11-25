from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: abstract = True

class Customer(TimeStamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="rockmaster_customer")
    name = models.CharField(max_length=180)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    billing_address = models.TextField(blank=True)
    default_delivery_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.name

class Supplier(TimeStamped):
    name = models.CharField(max_length=180)
    contact_person = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    location = models.CharField(max_length=180, blank=True)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Product(TimeStamped):
    class Category(models.TextChoices):
        GRANITE_DUST = "granite_dust", "Granite Dust"
        GRANITE_STONE = "granite_stone", "Granite Stones"
        SHARP_SAND = "sharp_sand", "Sharp Sand"
        LATERITE = "laterite", "Laterite"
        HAULAGE = "haulage", "Haulage Service"
        OTHER = "other", "Other"
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=30, choices=Category.choices)
    active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    unit_rate = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0"))])
    unit_label = models.CharField(max_length=30, default="tonne")
    per_tonne_rate = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0"))])
    per_truck_rate = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0"))])
    image = models.ImageField(upload_to="product_images/", blank=True)
    def __str__(self): return self.name

class Truck(TimeStamped):
    registration_number = models.CharField(max_length=30, unique=True)
    truck_type = models.CharField(max_length=80, blank=True)
    capacity_tonnes = models.DecimalField(max_digits=9, decimal_places=2, null=True, blank=True)
    capacity_description = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    def __str__(self): return self.registration_number

class Driver(TimeStamped):
    full_name = models.CharField(max_length=160)
    phone = models.CharField(max_length=30, blank=True)
    licence_number = models.CharField(max_length=80, blank=True)
    active = models.BooleanField(default=True)
    def __str__(self): return self.full_name

class Order(TimeStamped):
    class PricingBasis(models.TextChoices):
        PER_TONNE = "tonne", "Per tonne"
        PER_TRUCK = "truck", "Per truck"
    class Status(models.TextChoices):
        ENQUIRY = "enquiry", "Enquiry"
        QUOTED = "quoted", "Quoted"
        CONFIRMED = "confirmed", "Confirmed"
        SOURCING = "sourcing", "Sourcing"
        DISPATCHED = "dispatched", "Dispatched"
        DELIVERED = "delivered", "Delivered"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
    order_number = models.CharField(max_length=30, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    pricing_basis = models.CharField(max_length=10, choices=PricingBasis.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit_rate = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    delivery_address = models.TextField()
    order_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.ENQUIRY)
    notes = models.TextField(blank=True)
    delivery_charge = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    requires_quote = models.BooleanField(default=False)
    quote_status = models.CharField(max_length=16, choices=[("not_required","Not required"),("pending","Awaiting quotation"),("approved","Quotation approved"),("declined","Quotation declined")], default="not_required")
    guest_token = models.UUIDField(default=__import__("uuid").uuid4, editable=False, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_orders")
    @property
    def sales_total(self):
        items = getattr(self, "items", None)
        if items is not None and items.exists():
            return sum((item.line_total for item in items.all()), Decimal("0")) + self.delivery_charge
        return self.quantity * self.unit_rate + self.delivery_charge
    def __str__(self): return self.order_number

class OrderItem(TimeStamped):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    pricing_basis = models.CharField(max_length=10, choices=Order.PricingBasis.choices)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    unit_rate = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    haulage_charge = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    requires_quote = models.BooleanField(default=False)
    @property
    def line_total(self):
        return self.quantity * self.unit_rate + self.haulage_charge
    def __str__(self):
        return f"{self.product.name} - {self.order.order_number}"

class Procurement(TimeStamped):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="procurements")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=2)
    purchase_date = models.DateField(default=timezone.localdate)
    reference = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    @property
    def total_cost(self): return self.quantity * self.unit_cost
    def __str__(self): return f"{self.order.order_number} - {self.supplier.name}"

class Dispatch(TimeStamped):
    class Status(models.TextChoices):
        PLANNED = "planned", "Planned"
        LOADED = "loaded", "Loaded"
        IN_TRANSIT = "in_transit", "In transit"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Delivery issue"
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="dispatches")
    truck = models.ForeignKey(Truck, on_delete=models.PROTECT)
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, null=True, blank=True)
    quantity_dispatched = models.DecimalField(max_digits=10, decimal_places=2)
    dispatch_time = models.DateTimeField(null=True, blank=True)
    delivery_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    delivery_note = models.TextField(blank=True)
    proof_of_delivery = models.FileField(upload_to="delivery_proofs/", blank=True)
    def __str__(self): return f"{self.order.order_number} - {self.truck.registration_number}"

class Invoice(TimeStamped):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="invoices")
    invoice_number = models.CharField(max_length=40, unique=True)
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    @property
    def total(self): return max(Decimal("0"), self.order.sales_total - self.discount)
    def __str__(self): return self.invoice_number

class Payment(TimeStamped):
    class Method(models.TextChoices):
        TRANSFER = "transfer", "Bank transfer"
        CASH = "cash", "Cash"
        POS = "pos", "POS"
        OTHER = "other", "Other"
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_date = models.DateField(default=timezone.localdate)
    method = models.CharField(max_length=12, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    notes = models.TextField(blank=True)
    def __str__(self): return f"{self.invoice.invoice_number} - {self.amount}"

class Expense(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending owner approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        PAID = "paid", "Paid"
    order = models.ForeignKey(Order, on_delete=models.PROTECT, null=True, blank=True, related_name="expenses")
    category = models.CharField(max_length=100)
    description = models.TextField()
    amount = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    expense_date = models.DateField(default=timezone.localdate)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="expense_requests")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="approved_expenses")
    approved_at = models.DateTimeField(null=True, blank=True)
    receipt = models.FileField(upload_to="expense_receipts/", blank=True)
    def approve(self, user):
        if not (user.is_superuser or user.groups.filter(name="Owner").exists()):
            raise PermissionError("Only the owner can approve expenses.")
        self.status, self.approved_by, self.approved_at = self.Status.APPROVED, user, timezone.now()
        self.save(update_fields=["status","approved_by","approved_at","updated_at"])
    def __str__(self): return f"{self.category} - {self.amount}"


class PaymentSubmission(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Awaiting verification"
        APPROVED = "approved", "Payment verified"
        REJECTED = "rejected", "Receipt rejected"
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="submissions")
    amount_claimed = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    payment_date = models.DateField(default=timezone.localdate)
    transfer_reference = models.CharField(max_length=120, blank=True)
    receipt = models.FileField(upload_to="customer_payment_receipts/")
    customer_note = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="reviewed_payment_submissions")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    def __str__(self): return f"{self.invoice.invoice_number} - {self.get_status_display()}"
