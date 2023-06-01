from django.urls import path, include
from .views import PlotsViewSet
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'plots', PlotsViewSet, basename='plots')


urlpatterns = [
    path('', include(router.urls)),
]
