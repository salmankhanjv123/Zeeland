from django.urls import path, include
from .views import ProjectsViewSet 
from rest_framework import routers


router = routers.DefaultRouter()
router.register(r'projects', ProjectsViewSet)


urlpatterns = [
    path('', include(router.urls)),
]
