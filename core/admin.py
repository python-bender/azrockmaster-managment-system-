from django.contrib import admin
from .models import Customer, Supplier, Product, Truck, Driver, Order, OrderItem, Procurement, Dispatch, Invoice, Payment, Expense, PaymentSubmission
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name","phone","email","created_at")
    search_fields = ("name","phone","email")
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("name","contact_person","phone","location","active")
    search_fields = ("name","phone","location")
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name","category","unit_rate","unit_label","per_tonne_rate","per_truck_rate","active")
    list_filter = ("category","active")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("order_number","customer","product","pricing_basis","quantity","unit_rate","status","order_date")
    list_filter = ("status","pricing_basis","order_date")
    search_fields = ("order_number","customer__name","product__name")
for model in (Truck, Driver, Procurement, Dispatch, Invoice, Payment, Expense, OrderItem, PaymentSubmission):
    admin.site.register(model)
