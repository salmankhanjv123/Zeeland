from django.urls import path, include
from .views import BookingViewSet, BookingForPaymentsListView, latest_booking_id
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'booking', BookingViewSet, basename='booking')


urlpatterns = [
    path('', include(router.urls)),
    path('booking-for-payments/', BookingForPaymentsListView.as_view()),
    path('booking/<int:project>/latest-booking/', latest_booking_id)
]
