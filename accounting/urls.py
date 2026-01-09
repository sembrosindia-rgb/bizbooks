"""
URL Configuration for Accounting API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrganizationViewSet, ChartOfAccountsViewSet, GeneralLedgerViewSet,
    PartyViewSet, InvoiceViewSet, AccountsPayableViewSet,
    AccountsReceivableViewSet, PaymentViewSet, GSTTransactionViewSet,
    TDSTransactionViewSet, TaxConfigurationViewSet, PurchaseOrderViewSet,
    PurchaseOrderLineItemViewSet, CreditNoteViewSet, CreditNoteLineItemViewSet,
    DebitNoteViewSet, DebitNoteLineItemViewSet, DocumentSequenceViewSet,
    BankAccountViewSet, BankTransactionViewSet, BankReconciliationViewSet,
    ExchangeRateViewSet, ForexGainLossViewSet, BankAPIConfigurationViewSet
)
from .user_views import (
    UserViewSet, RoleViewSet, PermissionViewSet, UserAuditLogViewSet,
    CustomFieldDefinitionViewSet, CustomFieldValueViewSet,
    CustomFormViewSet
)
from .user_views import SignUpView, VerifyEmailView
from .reporting_views import (
    DataImportViewSet, DataExportViewSet, FinancialReportViewSet,
    DashboardViewSet
)

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet)
router.register(r'chart-of-accounts', ChartOfAccountsViewSet, basename='coa')
router.register(r'general-ledger', GeneralLedgerViewSet, basename='general-ledger')
router.register(r'parties', PartyViewSet, basename='party')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'accounts-payable', AccountsPayableViewSet, basename='accounts-payable')
router.register(r'accounts-receivable', AccountsReceivableViewSet, basename='accounts-receivable')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'gst-transactions', GSTTransactionViewSet, basename='gst-transaction')
router.register(r'tds-transactions', TDSTransactionViewSet, basename='tds-transaction')
router.register(r'tax-config', TaxConfigurationViewSet, basename='tax-config')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'purchase-order-line-items', PurchaseOrderLineItemViewSet, basename='po-line-item')
router.register(r'credit-notes', CreditNoteViewSet, basename='credit-note')
router.register(r'credit-note-line-items', CreditNoteLineItemViewSet, basename='cn-line-item')
router.register(r'debit-notes', DebitNoteViewSet, basename='debit-note')
router.register(r'debit-note-line-items', DebitNoteLineItemViewSet, basename='dn-line-item')
router.register(r'document-sequences', DocumentSequenceViewSet, basename='document-sequence')

# Banking module endpoints
router.register(r'bank-accounts', BankAccountViewSet, basename='bank-account')
router.register(r'bank-transactions', BankTransactionViewSet, basename='bank-transaction')
router.register(r'bank-reconciliations', BankReconciliationViewSet, basename='bank-reconciliation')
router.register(r'exchange-rates', ExchangeRateViewSet, basename='exchange-rate')
router.register(r'forex-gains-losses', ForexGainLossViewSet, basename='forex-gain-loss')
router.register(r'bank-api-config', BankAPIConfigurationViewSet, basename='bank-api-config')

# User Management & RBAC endpoints
router.register(r'users', UserViewSet, basename='user')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'audit-logs', UserAuditLogViewSet, basename='audit-log')

# Custom Fields endpoints
router.register(r'custom-fields', CustomFieldDefinitionViewSet, basename='custom-field')
router.register(r'custom-field-values', CustomFieldValueViewSet, basename='custom-field-value')
router.register(r'custom-forms', CustomFormViewSet, basename='custom-form')

# Import/Export endpoints
router.register(r'import-jobs', DataImportViewSet, basename='import-job')
router.register(r'export-jobs', DataExportViewSet, basename='export-job')

# Financial Reporting endpoints
router.register(r'financial-reports', FinancialReportViewSet, basename='financial-report')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

app_name = 'accounting'

urlpatterns = [
    path('', include(router.urls)),
    path('auth/signup/', SignUpView.as_view()),
    path('auth/verify/', VerifyEmailView.as_view()),
]


