from django.urls import path, include
from .views import CustomersViewSet
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'customers', CustomersViewSet, basename='customers')


urlpatterns = [
    path('', include(router.urls)),
]
