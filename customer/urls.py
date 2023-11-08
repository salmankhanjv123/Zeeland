from django.urls import path, include
from .views import CustomersViewSet,CustomerMessagesListCreateView,CustomerMessagesDetailView
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'customers', CustomersViewSet, basename='customers')


urlpatterns = [
    path('', include(router.urls)),
    path('customer-messages/', CustomerMessagesListCreateView.as_view(), name='customer-messages-list'),
    path('customer-messages/<int:pk>/', CustomerMessagesDetailView.as_view(), name='customer-messages-detail'),
]
