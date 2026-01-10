from rest_framework import viewsets
from rest_framework.views import APIView
from .models import Organization, TaxConfiguration, Party, User

class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()

class TaxConfigurationViewSet(viewsets.ModelViewSet):
    queryset = TaxConfiguration.objects.all()

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()

# Add other ViewSets as pass for now
class ChartOfAccountsViewSet(viewsets.ModelViewSet):
    pass

class GeneralLedgerViewSet(viewsets.ModelViewSet):
    pass

class InvoiceViewSet(viewsets.ModelViewSet):
    pass

class AccountsPayableViewSet(viewsets.ModelViewSet):
    pass

class AccountsReceivableViewSet(viewsets.ModelViewSet):
    pass

class PaymentViewSet(viewsets.ModelViewSet):
    pass

class GSTTransactionViewSet(viewsets.ModelViewSet):
    pass

class TDSTransactionViewSet(viewsets.ModelViewSet):
    pass

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    pass

class PurchaseOrderLineItemViewSet(viewsets.ModelViewSet):
    pass

class CreditNoteViewSet(viewsets.ModelViewSet):
    pass

class CreditNoteLineItemViewSet(viewsets.ModelViewSet):
    pass

class DebitNoteViewSet(viewsets.ModelViewSet):
    pass

class DebitNoteLineItemViewSet(viewsets.ModelViewSet):
    pass

class DocumentSequenceViewSet(viewsets.ModelViewSet):
    pass

class BankAccountViewSet(viewsets.ModelViewSet):
    pass

class BankTransactionViewSet(viewsets.ModelViewSet):
    pass

class BankReconciliationViewSet(viewsets.ModelViewSet):
    pass

class ExchangeRateViewSet(viewsets.ModelViewSet):
    pass

class ForexGainLossViewSet(viewsets.ModelViewSet):
    pass

class BankAPIConfigurationViewSet(viewsets.ModelViewSet):
    pass

class DataImportViewSet(viewsets.ModelViewSet):
    pass

class DataExportViewSet(viewsets.ModelViewSet):
    pass

class FinancialReportViewSet(viewsets.ModelViewSet):
    pass

class DashboardViewSet(viewsets.ModelViewSet):
    pass

# Auth views
class SignUpView(APIView):
    pass

class VerifyEmailView(APIView):
    pass

class LoginView(APIView):
    pass

class LogoutView(APIView):
    pass