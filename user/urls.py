from django.urls import path, include
from .views import UserProjectsList, ProjectsList, UserViewSet, UserProjectsUpdate, UserProjectsDetail
from rest_framework import routers
router = routers.DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('users/all/projects/',
         UserProjectsList.as_view(), name='users_projects_list'),
    path('users/<int:id>/projects/',
         UserProjectsDetail.as_view(), name='users_projects_detail'),
    path('users/<int:pk>/projects/update/',
         UserProjectsUpdate.as_view(), name='users_projects_update'),
    path('projects/all/list/', ProjectsList.as_view(), name='projects_list'),
]
