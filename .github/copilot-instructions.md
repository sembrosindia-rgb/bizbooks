# GitHub Copilot / AI Agent Instructions for BizBooks

## TL;DR
BizBooks is a Django 4.2 + DRF accounting backend focused on Indian GST/TDS compliance (see `ARCHITECTURE.md`). Work at the service layer (`accounting/services.py`, `gst_calculator.py`, `tds_calculator.py`) for business logic; viewsets in `accounting/views.py` are thin and expect requests to be scoped by `organization_id` query parameter.

## Where to start (high value files)
- ARCHITECTURE.md — canonical design and data flows ✅
- QUICKSTART.md — environment, example commands and shell snippets ✅
- `accounting/models.py` — domain model and constraints (money fields use DecimalField with 2 dp)
- `accounting/services.py`, `gst_calculator.py`, `tds_calculator.py` — main business logic (unit test targets)
- `accounting/views.py` and `accounting/urls.py` — REST surface; uses DRF ViewSets and `DefaultRouter`
- `bizbooks/settings.py` — env-driven config (`python-decouple`), default DB=sqlite

## Project conventions & patterns (do these)
- All multi-entity operations must be atomic — use `@transaction.atomic` (see `InvoiceViewSet.create`).
- Scope queries by `organization_id` when calling APIs or writing tests (many viewsets return different queryset when `organization_id` passed).
- Business rules live in services/calculators — prefer testing and changing logic there, not inside viewsets.
- Use `InvoiceCreateSerializer` for invoice creation flows; follow existing serializer patterns for `create` vs `retrieve` behavior.
- Monetary values: always use `Decimal` and format/round to 2 decimals (paisa). Avoid floats.
- When adding new API endpoints, register the new ViewSet in `accounting/urls.py` router.
- For expensive imports/exports use background jobs (Celery + Redis); docs reference this in `DATA_IMPORT_EXPORT_REPORTING.md`.

## Testing & verification (what matters here)
- Unit test calculators (GST/TDS) for edge rates, reverse charge, and rounding behavior.
- Integration tests: full invoice lifecycle (create → calculate taxes → post → GL entries → AP/AR created → payment flows).
- Accounting invariants: GL debits == GL credits after posting; include a test asserting trial balance equality (see `GeneralLedgerService.get_trial_balance`).
- Add tests for `organization_id` scoping and RBAC permission enforcement for user endpoints.

## Debugging & local workflow
- Setup: `python -m venv venv && source venv/bin/activate && pip install -r requirements.txt` (see `QUICKSTART.md`).
- DB: defaults to `db.sqlite3` in project root; for prod switch to Postgres and set env vars in `.env` (see `settings.py`).
- Run migrations: `python manage.py migrate`; create superuser: `python manage.py createsuperuser`.
- Run server: `python manage.py runserver` — home page shows useful API quicklinks (see `bizbooks/urls.py` home_view HTML).
- Use `python manage.py shell` for quick service-level tests (examples in `QUICKSTART.md`).
- Logging: `LOGGING` is configured to output to console by default in `settings.py` — increase level if debugging.

## Security & infra notes
- Secrets and flags via `python-decouple` env variables — do not hardcode `SECRET_KEY` or `DEBUG=False` in PRs.
- Bank API credentials are intended to be encrypted and stored via `BankAPIConfiguration` (see `BANKING_MODULE.md`).
- Session-based auth is used by default (`SessionAuthentication`) and most endpoints require `IsAuthenticated`.

## When changing models / migrations
- Add `makemigrations` & `migrate` steps in the PR description; include the resulting migration files in the branch.
- Consider DB indexes for frequently queried fields (many models already include indexes; follow that style).

## Example quick checks for PR reviewers
- Does the change preserve GL invariants (debits == credits) for posted transactions? Include an automated assertion using `GeneralLedgerService.get_trial_balance` where applicable.
- Are decimals handled with `Decimal` and rounded to 2dp (paisa)? Any new monetary field must use `DecimalField(max_digits=16, decimal_places=2)` and code should use `Decimal`/`quantize` for rounding.
- Are long-running tasks offloaded to Celery (if applicable) instead of blocking requests? (See `DATA_IMPORT_EXPORT_REPORTING.md`.)
- Are APIs scoped by `organization_id` (or user org) where appropriate? Add tests that assert filtering behaviour.
- Are new public endpoints added to `accounting/urls.py` router and documented in `ARCHITECTURE.md` or a relevant doc?

## PR checklist (for reviewers) ✅
- GL invariant test: Add/verify a unit or integration test that asserts total debits == total credits after posting (use `GeneralLedgerService.get_trial_balance`).
- Decimal & rounding: Verify all monetary calculations use `Decimal` and round to 2 dp; include edge-case tests where GST/TDS produces fractional paisa.
- Organization scoping: Ensure `organization_id` query params are respected and add tests that call endpoints with/without `organization_id`.
- Atomicity: Changes that touch multiple entities must be wrapped in `@transaction.atomic`; add tests that simulate partial failures and verify rollback.
- Migrations: Include `makemigrations` results in the branch and list them in the PR summary; update `ARCHITECTURE.md` if schema semantics change.
- Background tasks: For heavy imports/exports, schedule Celery tasks and include a lightweight test that the Celery task is enqueued (or the service is called).
- RBAC & permissions: Add tests for permission-denied cases and ensure system roles (e.g., `is_system_role`) are not modifiable.
- Secrets & config: Confirm new secrets are read from env (via `python-decouple`) and not hard-coded.

## Testing templates (examples) 🔧
Use `pytest` + `pytest-django` for concise tests (recommended). If you prefer Django's test runner, similar assertions apply using `django.test.TestCase`.

File: `tests/unit/test_gst_calculator.py`
```python
from decimal import Decimal
import pytest

from accounting.gst_calculator import GSTCalculator
from accounting.models import Organization, TaxConfiguration, Party

@pytest.fixture
def org(db):
    o = Organization.objects.create(
        name="Test Org",
        registration_number="U1",
        gst_number="27TESTG1234A1Z0",
        pan="TESTPAN01",
        state="KA",
        address="",
        city="Bangalore",
        postal_code="560001",
        email="test@example.com",
        phone="",
        financial_year_start="2024-04-01",
        currency="INR"
    )
    TaxConfiguration.objects.create(
        organization=o,
        gst_rate_0_percent=0,
        gst_rate_5_percent=5,
        gst_rate_12_percent=12,
        gst_rate_18_percent=18,
        gst_rate_28_percent=28
    )
    return o

def test_calculate_line_item_gst_intra_state(org):
    calc = GSTCalculator(org)
    line = {
        'quantity': Decimal('10'),
        'unit_price': Decimal('1000'),
        'gst_rate': Decimal('18')
    }

    # seller and buyer in same state → CGST/SGST split
    result = calc.calculate_line_item_gst(line, seller_state='KA', buyer_state='KA')

    assert result['tax_amount'] == Decimal('1800.00')
    assert result['cgst_amount'] == Decimal('900.00')
    assert result['sgst_amount'] == Decimal('900.00')
    assert result['igst_amount'] == Decimal('0.00')


def test_rounding_behavior_for_paisa(org):
    calc = GSTCalculator(org)
    line = {
        'quantity': Decimal('1'),
        'unit_price': Decimal('0.3333'),
        'gst_rate': Decimal('18')
    }

    res = calc.calculate_line_item_gst(line, seller_state='KA', buyer_state='KA')
    # Assert amounts are rounded to 2 decimals
    assert res['tax_amount'].as_tuple().exponent >= -2
```

File: `tests/unit/test_tds_calculator.py`
```python
from decimal import Decimal
import pytest

from accounting.tds_calculator import TDSCalculator
from accounting.models import Organization, TaxConfiguration, Party

@pytest.fixture
def org(db):
    o = Organization.objects.create(
        name="Test Org",
        registration_number="U2",
        gst_number="27TESTG5678A1Z0",
        pan="TESTPAN02",
        state="KA",
        address="",
        city="Bangalore",
        postal_code="560001",
        email="test2@example.com",
        phone="",
        financial_year_start="2024-04-01",
        currency="INR"
    )
    TaxConfiguration.objects.create(
        organization=o,
        tds_rate_contractor=10
    )
    return o

def test_tds_threshold_and_amount(org):
    calc = TDSCalculator(org)
    res = calc.calculate_tds(gross_payment=Decimal('100000.00'), nature='CONTRACTOR')
    assert res['tds_amount'] == Decimal('10000.00')
    assert res['net_payment'] == Decimal('90000.00')
```

### How to run
- Run with pytest (recommended): `pytest tests/unit -q`
- Or run Django tests: `python manage.py test tests.unit`

---
If anything here is unclear or you want extra examples (e.g., a template unit test for GST/TDS calculators or a checklist to enforce GL balances in CI), tell me which part to expand and I will iterate. 👋
