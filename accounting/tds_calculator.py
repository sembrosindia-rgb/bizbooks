from decimal import Decimal, ROUND_HALF_UP

try:
    from accounting.models import TaxConfiguration
except Exception:
    TaxConfiguration = None


class TDSCalculator:
    def __init__(self, organization):
        self.organization = organization
        self.config = None
        if TaxConfiguration is not None:
            try:
                self.config = TaxConfiguration.objects.filter(organization=organization).first()
            except Exception:
                self.config = None

    def _quantize(self, amount: Decimal) -> Decimal:
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def _get_rate_for_nature(self, nature: str) -> Decimal:
        if not self.config:
            return Decimal('0')
        nature_upper = (nature or '').upper()
        if 'CONTRACTOR' in nature_upper:
            return Decimal(getattr(self.config, 'tds_rate_contractor', 0))
        return Decimal('0')

    def calculate_tds(self, gross_payment: Decimal, nature: str) -> dict:
        rate = self._get_rate_for_nature(nature)
        tds_amount = self._quantize(gross_payment * rate / Decimal('100'))
        net_payment = self._quantize(gross_payment - tds_amount)
        return {'tds_amount': tds_amount, 'net_payment': net_payment}
