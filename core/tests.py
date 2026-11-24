from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Customer, Product, Order
class OrderCalculationTests(TestCase):
    def test_two_trucks_at_370000_each(self):
        user = get_user_model().objects.create_user(username="owner", password="test-pass-123")
        customer = Customer.objects.create(name="Test Customer")
        product = Product.objects.create(name="Sharp Sand", category=Product.Category.SHARP_SAND)
        order = Order.objects.create(order_number="AZR-TEST-001", customer=customer, product=product,
            pricing_basis=Order.PricingBasis.PER_TRUCK, quantity=2, unit_rate=Decimal("370000"),
            delivery_address="Wuse Zone 3, Abuja", created_by=user)
        self.assertEqual(order.sales_total, Decimal("740000"))
