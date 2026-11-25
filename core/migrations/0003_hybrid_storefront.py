import decimal
import uuid
import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("core", "0002_customer_portal")]
    operations = [
        migrations.AddField(model_name="product", name="per_tonne_rate", field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))])),
        migrations.AddField(model_name="product", name="per_truck_rate", field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))])),
        migrations.AddField(model_name="product", name="image", field=models.ImageField(blank=True, upload_to="product_images/")),
        migrations.AddField(model_name="order", name="delivery_charge", field=models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
        migrations.AddField(model_name="order", name="requires_quote", field=models.BooleanField(default=False)),
        migrations.AddField(model_name="order", name="quote_status", field=models.CharField(choices=[("not_required","Not required"),("pending","Awaiting quotation"),("approved","Quotation approved"),("declined","Quotation declined")], default="not_required", max_length=16)),
        migrations.AddField(model_name="order", name="guest_token", field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        migrations.CreateModel(name="OrderItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("pricing_basis", models.CharField(choices=[("tonne","Per tonne"),("truck","Per truck")], max_length=10)),
            ("quantity", models.DecimalField(decimal_places=2, max_digits=10, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0.01"))])),
            ("unit_rate", models.DecimalField(decimal_places=2, max_digits=14, validators=[django.core.validators.MinValueValidator(decimal.Decimal("0"))])),
            ("haulage_charge", models.DecimalField(decimal_places=2, default=decimal.Decimal("0.00"), max_digits=14)),
            ("requires_quote", models.BooleanField(default=False)),
            ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="core.order")),
            ("product", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to="core.product")),
        ]),
    ]
