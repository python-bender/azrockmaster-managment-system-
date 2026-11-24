# AZ Rockmaster Cloud — Phase 1 + Initial Business Interface

A Django foundation for AZ ROCKMASTER ABUJA.

## Configured business rules
- Sales can be priced per tonne or per truck.
- Materials are procured directly against customer orders.
- Expenses are submitted as pending and only users in the `Owner` group (or superusers) can approve/reject them.
- No warehouse stock ledger is included in this initial order-based version.

## Run locally
1. Install Python 3.11+.
2. Create and activate a virtual environment.
3. `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and set a strong `DJANGO_SECRET_KEY`.
5. `python manage.py makemigrations core`
6. `python manage.py migrate`
7. `python manage.py createsuperuser`
8. `python manage.py runserver`
9. Open `http://127.0.0.1:8000/accounts/login/`.

## Initial interface
Dashboard, customers, suppliers, products, order entry, expense submission/owner approval, and truck/driver records are included. The Django admin remains available at `/admin/`.

## Production checklist
This package is not deployed online yet. Before using real records:
- Set `DEBUG=False`, a unique secret key and the deployed hostname in environment variables.
- Configure persistent managed PostgreSQL and durable file storage.
- Enable HTTPS and automated backups; test a restore.
- Create an `Owner` group and add only the business owner to it.
- Assign staff to least-privilege groups.
- Add full invoice PDF/PNG rendering, payment entry screens, delivery workflow and reporting in subsequent phases.
"# azrockmaster-managment-system-" 
