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
