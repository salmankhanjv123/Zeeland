from django.urls import path, include
from .views import (
    BookingViewSet,
    BookingForPaymentsListView,
    TokenViewSet,
    latest_booking_id,
    PlotResaleViewSet,
    RefundTokenViewSet,
    UpdateTokenStatusView,
)
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r"booking", BookingViewSet, basename="booking")
router.register(r"plot-token", TokenViewSet, basename="token")
router.register(r"plot-resale", PlotResaleViewSet, basename="plot-resale")


urlpatterns = [
    path("", include(router.urls)),
    path("booking-for-payments/", BookingForPaymentsListView.as_view()),
    path("booking/<int:project>/latest-booking/", latest_booking_id),
    path("plot-token/<int:token_id>/token-refund/", RefundTokenViewSet.as_view()),
    path("plot-token/<int:token_id>/update-status/", UpdateTokenStatusView.as_view()),
]
