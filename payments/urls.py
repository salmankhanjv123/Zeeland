from django.urls import path, include
from .views import (
    IncomingFundViewSet,
    OutgoingFundViewSet,
    ExpenseTypeViewSet,
    JournalVoucherViewSet,
    DuePaymentsView,
    PaymentReminderViewSet,
    ExpensePersonViewSet,
    BankViewSet,
)
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r"payments", IncomingFundViewSet, basename="payments")
router.register(r"expenses", OutgoingFundViewSet, basename="expenses")
router.register(r"journal-voucher", JournalVoucherViewSet, basename="journal-voucher")
router.register(r"expense-type", ExpenseTypeViewSet, basename="expense-type")
router.register(
    r"payments-reminder", PaymentReminderViewSet, basename="payments-reminder"
)
router.register(r"expense-persons", ExpensePersonViewSet, basename="expense-persons")
router.register(r"banks", BankViewSet, basename="banks")


urlpatterns = [
    path("", include(router.urls)),
    path("due-payments/", DuePaymentsView.as_view(), name="due_payments"),
]
