from django.urls import path
from .views import IncomingFundReportView, OutgoingFundReportView, JournalVoucherReportView, TotalCountView, TotalAmountView, MonthlyIncomingFundGraphView, AnnualIncomingFundGraphView
urlpatterns = [
    path('incoming-fund-report/', IncomingFundReportView.as_view()),
    path('outgoing-fund-report/', OutgoingFundReportView.as_view()),
    path('journal-voucher-report/', JournalVoucherReportView.as_view()),
    path('dashboard-counts/', TotalCountView.as_view()),
    path('dashboard-amounts/', TotalAmountView.as_view()),
    path('monthly-incoming-fund/', MonthlyIncomingFundGraphView.as_view()),
    path('annual-incoming-fund/', AnnualIncomingFundGraphView.as_view())
]
