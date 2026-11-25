from django import forms
from .models import Customer, Supplier, Product, Order, Expense, Truck, Driver, Procurement, Dispatch, Invoice, Payment

class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

class CustomerForm(StyledModelForm):
    class Meta:
        model = Customer
        fields = ["name", "phone", "email", "billing_address", "default_delivery_address", "notes"]

class SupplierForm(StyledModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "contact_person", "phone", "location", "notes", "active"]

class ProductForm(StyledModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "description", "unit_rate", "unit_label", "per_tonne_rate", "per_truck_rate", "image", "active"]

class OrderForm(StyledModelForm):
    class Meta:
        model = Order
        fields = ["order_number", "customer", "product", "pricing_basis", "quantity", "unit_rate", "delivery_address", "order_date", "notes"]
        widgets = {"order_date": forms.DateInput(attrs={"type": "date"})}

class ExpenseForm(StyledModelForm):
    class Meta:
        model = Expense
        fields = ["order", "category", "description", "amount", "expense_date", "receipt"]
        widgets = {"expense_date": forms.DateInput(attrs={"type": "date"})}

class TruckForm(StyledModelForm):
    class Meta:
        model = Truck
        fields = ["registration_number", "truck_type", "capacity_tonnes", "capacity_description", "active", "notes"]

class DriverForm(StyledModelForm):
    class Meta:
        model = Driver
        fields = ["full_name", "phone", "licence_number", "active"]
