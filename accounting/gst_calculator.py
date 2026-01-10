from decimal import Decimal, ROUND_HALF_UP


class GSTCalculator:
    def __init__(self, organization):
        self.organization = organization

    def _quantize(self, amount: Decimal) -> Decimal:
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

    def calculate_line_item_gst(self, line: dict, seller_state: str | None = None, buyer_state: str | None = None) -> dict:
        qty = Decimal(line.get('quantity', 0))
        unit_price = Decimal(line.get('unit_price', 0))
        gst_rate = Decimal(line.get('gst_rate', 0))

        taxable = qty * unit_price
        tax_amount = self._quantize(taxable * gst_rate / Decimal('100'))

        if seller_state and buyer_state and seller_state == buyer_state:
            half = self._quantize(tax_amount / Decimal('2'))
            cgst = half
            sgst = half
            igst = Decimal('0.00')
        else:
            cgst = Decimal('0.00')
            sgst = Decimal('0.00')
            igst = tax_amount

        return {
            'tax_amount': tax_amount,
            'cgst_amount': cgst,
            'sgst_amount': sgst,
            'igst_amount': igst,
        }
