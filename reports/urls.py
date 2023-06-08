from django.urls import path
from .views import IncomingFundReportView, OutgoingFundReportView, JournalVoucherReportView
urlpatterns = [
    path('incoming-fund-report/', IncomingFundReportView.as_view()),
    path('outgoing-fund-report/', OutgoingFundReportView.as_view()),
    path('journal-voucher-report/', JournalVoucherReportView.as_view()),
]
