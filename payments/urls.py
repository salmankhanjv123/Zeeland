from django.urls import path, include
from .views import IncomingFundViewSet, OutgoingFundViewSet, ExpenseTypeViewSet, JournalVoucherViewSet, DuePaymentsView
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'payments', IncomingFundViewSet, basename='payments')
router.register(r'expenses', OutgoingFundViewSet, basename='expenses')
router.register(r'journal-voucher', JournalVoucherViewSet,
                basename='journal-voucher')
router.register(r'expense-type', ExpenseTypeViewSet, basename='expense-type')


urlpatterns = [
    path('', include(router.urls)),
    path('due-payments/', DuePaymentsView.as_view(), name='due_payments'),
]
