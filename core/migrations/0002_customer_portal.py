from decimal import Decimal
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0001_initial"), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.AddField(model_name="customer", name="user", field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="rockmaster_customer", to=settings.AUTH_USER_MODEL)),
        migrations.AddField(model_name="product", name="unit_rate", field=models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0"))])),
        migrations.AddField(model_name="product", name="unit_label", field=models.CharField(default="tonne", max_length=30)),
        migrations.AlterField(model_name="order", name="created_by", field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="created_orders", to=settings.AUTH_USER_MODEL)),
        migrations.CreateModel(name="PaymentSubmission", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("amount_claimed", models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(Decimal("0.01"))])),
            ("payment_date", models.DateField(default=django.utils.timezone.localdate)),
            ("transfer_reference", models.CharField(blank=True, max_length=120)),
            ("receipt", models.FileField(upload_to="customer_payment_receipts/")),
            ("customer_note", models.TextField(blank=True)),
            ("status", models.CharField(choices=[("pending","Awaiting verification"),("approved","Payment verified"),("rejected","Receipt rejected")], default="pending", max_length=12)),
            ("reviewed_at", models.DateTimeField(blank=True, null=True)), ("review_note", models.TextField(blank=True)),
            ("invoice", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="submissions", to="core.invoice")),
            ("reviewed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="reviewed_payment_submissions", to=settings.AUTH_USER_MODEL)),
        ]),
    ]
