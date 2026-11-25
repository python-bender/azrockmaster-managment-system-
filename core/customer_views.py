import uuid
from decimal import Decimal
from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from .models import Customer, Product, Order, Invoice, Payment, PaymentSubmission

class CustomerRegistrationForm(forms.Form):
    full_name = forms.CharField(max_length=180)
    email = forms.EmailField()
    phone = forms.CharField(max_length=30)
    username = forms.CharField(max_length=150)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"
    def clean(self):
        cleaned = super().clean()
        if len(cleaned.get("password1", "")) < 12:
            self.add_error("password1", "Use at least 12 characters.")
        if User.objects.filter(email__iexact=cleaned.get("email", "")).exists():
            self.add_error("email", "An account with this email already exists.")
        if cleaned.get("password1") != cleaned.get("password2"):
            self.add_error("password2", "Passwords do not match.")
        if User.objects.filter(username=cleaned.get("username")).exists():
            self.add_error("username", "This username is already taken.")
        return cleaned
    def save(self):
        user = User.objects.create_user(username=self.cleaned_data["username"], email=self.cleaned_data["email"], password=self.cleaned_data["password1"])
        Customer.objects.create(user=user, name=self.cleaned_data["full_name"], email=user.email, phone=self.cleaned_data["phone"])
        return user

def _send_customer_email(subject, body, recipient):
    if recipient:
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient], fail_silently=True)

def customer_register(request):
    if request.user.is_authenticated:
        return redirect("customer-portal")
    form = CustomerRegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your customer account is ready.")
        return redirect("customer-portal")
    return render(request, "customer/register.html", {"form": form})

def customer_portal(request):
    if request.user.is_authenticated:
        customer = Customer.objects.filter(user=request.user).first()
        if customer:
            orders = Order.objects.filter(customer=customer).select_related("product").order_by("-created_at")
            return render(request, "customer/portal.html", {"customer": customer, "orders": orders})
    return render(request, "customer/portal.html", {"customer": None, "orders": []})

def customer_order(request):
    products = Product.objects.filter(active=True).order_by("name")
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip()
        phone = request.POST.get("phone", "").strip()
        address = request.POST.get("delivery_address", "").strip()
        product = get_object_or_404(Product, pk=request.POST.get("product"), active=True)
        try:
            quantity = Decimal(request.POST.get("quantity", "0"))
        except Exception:
            quantity = Decimal("0")
        if not name or not email or not phone or not address or quantity <= 0:
            messages.error(request, "Complete all required details and enter a valid quantity.")
        elif product.unit_rate <= 0:
            messages.error(request, "This product is not yet available for online ordering. Please contact AZ ROCKMASTER for a quotation.")
        else:
            customer = None
            if request.user.is_authenticated:
                customer = Customer.objects.filter(user=request.user).first()
            if customer is None:
                customer = Customer.objects.filter(email__iexact=email).first()
            if customer is None:
                customer = Customer.objects.create(name=name, email=email, phone=phone, default_delivery_address=address)
            else:
                customer.name, customer.email, customer.phone = name, email, phone
                customer.default_delivery_address = address
                customer.save()
            order = Order.objects.create(
                order_number="AZR-" + timezone.localdate().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:6].upper(),
                customer=customer, product=product,
                pricing_basis=Order.PricingBasis.PER_TRUCK if product.unit_label.lower() in ["truck", "per truck"] else Order.PricingBasis.PER_TONNE,
                quantity=quantity, unit_rate=product.unit_rate, delivery_address=address,
                status=Order.Status.QUOTED, created_by=request.user if request.user.is_authenticated else None,
                notes=request.POST.get("notes", "").strip()
            )
            invoice = Invoice.objects.create(order=order, invoice_number="AZR-INV-" + timezone.localdate().strftime("%Y") + "-" + uuid.uuid4().hex[:7].upper())
            invoice_url = request.build_absolute_uri("/customer/invoice/" + str(invoice.pk) + "/?access=" + invoice.invoice_number)
            _send_customer_email("AZ ROCKMASTER order received - " + order.order_number,
                "Thank you for your order. Your invoice " + invoice.invoice_number + " is ready: " + invoice_url +
                "\nOrder value: NGN " + str(invoice.total) + "\nYour order is awaiting payment and verification.", email)
            _send_customer_email("New customer order: " + order.order_number,
                "A new online order has been placed. Customer: " + name + " (" + phone + "). Invoice: " + invoice.invoice_number +
                ". Review it in the staff dashboard.", getattr(settings, "ORDER_NOTIFICATION_EMAIL", ""))
            messages.success(request, "Your order has been submitted. Your invoice number is " + invoice.invoice_number + ".")
            return redirect("/customer/invoice/" + str(invoice.pk) + "/?access=" + invoice.invoice_number) if not request.user.is_authenticated else redirect("customer-invoice", pk=invoice.pk)
    return render(request, "customer/order.html", {"products": products})

def _invoice_access(request, invoice):
    if request.user.is_staff or request.user.is_superuser:
        return True
    customer = Customer.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    return bool(customer and invoice.order.customer_id == customer.id)

def customer_invoice(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("order__customer", "order__product"), pk=pk)
    if not _invoice_access(request, invoice):
        # Guest invoice is accessible only through its unguessable invoice URL token.
        token = request.GET.get("access", "")
        if token != invoice.invoice_number:
            raise PermissionDenied
    return render(request, "customer/invoice.html", {"invoice": invoice})

def customer_upload_receipt(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related("order__customer"), pk=pk)
    if not _invoice_access(request, invoice) and request.GET.get("access", "") != invoice.invoice_number and request.POST.get("access", "") != invoice.invoice_number:
        raise PermissionDenied
    if request.method == "POST":
        receipt = request.FILES.get("receipt")
        amount = request.POST.get("amount_claimed", "0")
        try:
            amount = Decimal(amount)
        except Exception:
            amount = Decimal("0")
        if not receipt or amount <= 0:
            messages.error(request, "Upload a receipt and enter the amount paid.")
        elif receipt.size > 5 * 1024 * 1024:
            messages.error(request, "Receipt must not exceed 5 MB.")
        elif receipt.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
            messages.error(request, "Upload a JPG, PNG or PDF receipt.")
        else:
            PaymentSubmission.objects.create(invoice=invoice, amount_claimed=amount, receipt=receipt,
                transfer_reference=request.POST.get("transfer_reference", "").strip(),
                customer_note=request.POST.get("customer_note", "").strip())
            messages.success(request, "Receipt submitted. It is awaiting verification; your order is not marked paid yet.")
            _send_customer_email("Payment receipt received - " + invoice.invoice_number,
                "We received your payment evidence. It will be reviewed by AZ ROCKMASTER. This is not yet payment confirmation.", invoice.order.customer.email)
            return redirect("customer-invoice", pk=invoice.pk) if request.user.is_authenticated else redirect("/customer/invoice/" + str(invoice.pk) + "/?access=" + invoice.invoice_number)
    return render(request, "customer/upload_receipt.html", {"invoice": invoice, "access_token": request.GET.get("access", "")})

def staff_can_verify(user):
    return user.is_staff or user.is_superuser or user.groups.filter(name__in=["Owner", "Accountant"]).exists()

@login_required
@user_passes_test(staff_can_verify)
def payment_submissions(request):
    rows = PaymentSubmission.objects.select_related("invoice__order__customer", "invoice__order__product", "reviewed_by").order_by("-created_at")
    return render(request, "customer/payment_submissions.html", {"rows": rows})

@login_required
@user_passes_test(staff_can_verify)
@require_POST
@transaction.atomic
def review_payment_submission(request, pk, decision):
    submission = get_object_or_404(PaymentSubmission.objects.select_for_update().select_related("invoice__order__customer"), pk=pk)
    if submission.status != PaymentSubmission.Status.PENDING:
        messages.info(request, "This receipt has already been reviewed.")
        return redirect("payment-submissions")
    note = request.POST.get("review_note", "").strip()
    if decision == "approve":
        Payment.objects.create(invoice=submission.invoice, amount=submission.amount_claimed,
            payment_date=submission.payment_date, method=Payment.Method.TRANSFER,
            reference=submission.transfer_reference, received_by=request.user,
            notes="Verified from customer receipt submission.")
        submission.status = PaymentSubmission.Status.APPROVED
        submission.invoice.order.status = Order.Status.CONFIRMED
        submission.invoice.order.save(update_fields=["status", "updated_at"])
        _send_customer_email("Payment confirmed - " + submission.invoice.invoice_number,
            "Your payment has been verified by AZ ROCKMASTER. Your order is now confirmed.", submission.invoice.order.customer.email)
        messages.success(request, "Payment recorded and order confirmed. Ensure the bank credit was independently checked.")
    elif decision == "reject":
        submission.status = PaymentSubmission.Status.REJECTED
        submission.review_note = note or "Please contact AZ ROCKMASTER for clarification."
        _send_customer_email("Payment receipt needs attention - " + submission.invoice.invoice_number,
            "Your payment evidence could not be approved. Reason: " + submission.review_note, submission.invoice.order.customer.email)
        messages.warning(request, "Receipt rejected; the customer will be notified.")
    else:
        messages.error(request, "Invalid review action.")
        return redirect("payment-submissions")
    submission.reviewed_by = request.user
    submission.reviewed_at = timezone.now()
    submission.save()
    return redirect("payment-submissions")
