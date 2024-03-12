from django.urls import path, include
from .views import ProjectsViewSet ,BalanceSheetViewSet
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'projects', ProjectsViewSet)
router.register(r'balance-sheet', BalanceSheetViewSet,basename="balance-sheet")


urlpatterns = [
    path('', include(router.urls)),
    # path("projects-balance/bulk-update/",ProjectsBalanceBulkUpdateCreateAPIView.as_view())
]
