from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Sum, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Customer, Supplier, Product, Order, Expense, Invoice, Payment, Procurement, Dispatch, Truck, Driver
from .forms import CustomerForm, SupplierForm, ProductForm, OrderForm, ExpenseForm, TruckForm, DriverForm

def owner_check(user):
    return user.is_superuser or user.groups.filter(name="Owner").exists()

def owner_required(view):
    return user_passes_test(owner_check)(view)

@login_required
def dashboard(request):
    orders = Order.objects.exclude(status=Order.Status.CANCELLED)
    sales = sum((o.sales_total for o in orders), Decimal("0"))
    paid = Payment.objects.aggregate(v=Sum("amount"))["v"] or Decimal("0")
    approved_expenses = Expense.objects.filter(status__in=[Expense.Status.APPROVED, Expense.Status.PAID]).aggregate(v=Sum("amount"))["v"] or Decimal("0")
    procurement_cost = sum((x.total_cost for x in Procurement.objects.all()), Decimal("0"))
    context = {
        "sales": sales, "paid": paid, "receivables": max(sales-paid, Decimal("0")),
        "approved_expenses": approved_expenses, "procurement_cost": procurement_cost,
        "order_count": orders.count(), "customer_count": Customer.objects.count(),
        "pending_expenses": Expense.objects.filter(status=Expense.Status.PENDING).count(),
        "recent_orders": orders.select_related("customer","product").order_by("-created_at")[:8],
    }
    return render(request, "core/dashboard.html", context)

@login_required
def customers(request):
    rows = Customer.objects.order_by("-created_at")
    page = Paginator(rows, 20).get_page(request.GET.get("page"))
    return render(request, "core/list.html", {"title":"Customers", "rows":page, "columns":["name","phone","email"], "create_url":"customer-create"})

@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        form.save(); messages.success(request, "Customer saved."); return redirect("customers")
    return render(request, "core/form.html", {"form":form,"title":"Add customer"})

@login_required
def suppliers(request):
    rows = Supplier.objects.order_by("-created_at")
    return render(request, "core/list.html", {"title":"Suppliers","rows":rows,"columns":["name","contact_person","phone","location"],"create_url":"supplier-create"})

@login_required
def supplier_create(request):
    form = SupplierForm(request.POST or None)
    if form.is_valid():
        form.save(); messages.success(request,"Supplier saved."); return redirect("suppliers")
    return render(request,"core/form.html",{"form":form,"title":"Add supplier"})

@login_required
def products(request):
    rows = Product.objects.order_by("name")
    return render(request,"core/list.html",{"title":"Products","rows":rows,"columns":["name","category","active"],"create_url":"product-create"})

@login_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if form.is_valid():
        form.save(); messages.success(request,"Product saved."); return redirect("products")
    return render(request,"core/form.html",{"form":form,"title":"Add product"})

@login_required
def orders(request):
    rows = Order.objects.select_related("customer","product").order_by("-created_at")
    return render(request,"core/orders.html",{"rows":rows})

@login_required
def order_create(request):
    form = OrderForm(request.POST or None)
    if form.is_valid():
        order = form.save(commit=False); order.created_by = request.user; order.save()
        messages.success(request, f"Order {order.order_number} created."); return redirect("orders")
    return render(request,"core/form.html",{"form":form,"title":"Create order"})

@login_required
def expenses(request):
    rows = Expense.objects.select_related("requested_by","approved_by","order").order_by("-created_at")
    return render(request,"core/expenses.html",{"rows":rows,"can_approve":owner_check(request.user)})

@login_required
def expense_create(request):
    form = ExpenseForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        expense = form.save(commit=False); expense.requested_by = request.user
        expense.status = Expense.Status.PENDING
        expense.save()
        messages.success(request,"Expense submitted for owner approval."); return redirect("expenses")
    return render(request,"core/form.html",{"form":form,"title":"Submit expense"})

@login_required
@owner_required
def expense_decision(request, pk, decision):
    if request.method != "POST": return redirect("expenses")
    expense = get_object_or_404(Expense, pk=pk)
    if decision == "approve":
        expense.approve(request.user)
        messages.success(request,"Expense approved.")
    elif decision == "reject":
        expense.status = Expense.Status.REJECTED
        expense.approved_by = request.user
        expense.approved_at = timezone.now()
        expense.save(update_fields=["status","approved_by","approved_at","updated_at"])
        messages.info(request,"Expense rejected.")
    return redirect("expenses")

@login_required
def fleet(request):
    return render(request,"core/fleet.html",{"trucks":Truck.objects.all(),"drivers":Driver.objects.all()})

@login_required
def truck_create(request):
    form=TruckForm(request.POST or None)
    if form.is_valid(): form.save(); messages.success(request,"Truck saved."); return redirect("fleet")
    return render(request,"core/form.html",{"form":form,"title":"Add truck"})

@login_required
def driver_create(request):
    form=DriverForm(request.POST or None)
    if form.is_valid(): form.save(); messages.success(request,"Driver saved."); return redirect("fleet")
    return render(request,"core/form.html",{"form":form,"title":"Add driver"})


# Temporary first-owner bootstrap. Remove INITIAL_ADMIN_SETUP_TOKEN from the
# hosting environment immediately after creating the first superuser.
import os
import secrets
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.views.decorators.http import require_http_methods

@require_http_methods(["GET", "POST"])
def initial_admin_setup(request):
    User = get_user_model()
    if User.objects.filter(is_superuser=True).exists():
        return render(request, "core/setup_closed.html", status=410)

    setup_token = os.environ.get("INITIAL_ADMIN_SETUP_TOKEN", "")
    if not setup_token:
        return render(request, "core/setup_unavailable.html", status=503)

    error = ""
    if request.method == "POST":
        supplied_token = request.POST.get("setup_token", "")
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        if not secrets.compare_digest(supplied_token, setup_token):
            error = "The setup key is incorrect."
        elif password != password_confirm:
            error = "The passwords do not match."
        elif len(password) < 12:
            error = "Use a password with at least 12 characters."
        else:
            user = User.objects.create_superuser(
                username="azrockmaster",
                email=request.POST.get("email", "").strip(),
                password=password,
            )
            owner_group, _ = Group.objects.get_or_create(name="Owner")
            user.groups.add(owner_group)
            return render(request, "core/setup_complete.html")

    return render(request, "core/initial_admin_setup.html", {"error": error})
