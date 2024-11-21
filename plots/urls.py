from django.urls import path, include
from .views import PlotsViewSet, ResalePlotListView,BlockViewSet
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'plots', PlotsViewSet, basename='plots')
router.register(r'blocks', BlockViewSet, basename='blocks')


urlpatterns = [
    path('', include(router.urls)),
    path('resold-plots/', ResalePlotListView.as_view()),
]
