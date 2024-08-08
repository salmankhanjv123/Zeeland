from django.urls import path
from .views import (
    IncomingFundReportView,
    OutgoingFundReportView,
    JournalVoucherReportView,
    TotalCountView,
    TotalAmountView,
    MonthlyIncomingFundGraphView,
    AnnualIncomingFundGraphView,
    DealerLedgerView,
    CustomerLedgerView,
    PlotLedgerView,
    BalanceSheetView,
    IncomingPaymentsReport,
    IncomingChequeReport,
    OutgoingPaymentsReport,
)

urlpatterns = [
    path("incoming-fund-report/", IncomingFundReportView.as_view()),
    path("incoming-payment-report/", IncomingPaymentsReport.as_view()),
    path("incoming-cheque-report/", IncomingChequeReport.as_view()),
    
    path("outgoing-fund-report/", OutgoingFundReportView.as_view()),
    path("outgoing-payment-report/", OutgoingPaymentsReport.as_view()),
    path("journal-voucher-report/", JournalVoucherReportView.as_view()),
    path("dashboard-counts/", TotalCountView.as_view()),
    path("dashboard-amounts/", TotalAmountView.as_view()),
    path("monthly-incoming-fund/", MonthlyIncomingFundGraphView.as_view()),
    path("annual-incoming-fund/", AnnualIncomingFundGraphView.as_view()),
    path("dealer-ledger/", DealerLedgerView.as_view()),
    path("customer-ledger/", CustomerLedgerView.as_view()),
    
    path("plot-ledger/", PlotLedgerView.as_view()),
    path("balance-report/", BalanceSheetView.as_view()),
]
