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
