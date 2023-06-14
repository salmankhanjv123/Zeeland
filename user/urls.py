from django.urls import path, include
from .views import UserProjectsList, ProjectsList, UserViewSet, UserProjectsUpdate, UserProjectsDetail, GroupListCreateAPIView, GroupRetrieveUpdateDestroyAPIView, PermissionListCreateAPIView, PermissionRetrieveUpdateDestroyAPIView, UserAssignGroupView, UserAssignPermissionView
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
    path('groups/', GroupListCreateAPIView.as_view(), name='group-list'),
    path('groups/<int:pk>/', GroupRetrieveUpdateDestroyAPIView.as_view(),
         name='group-detail'),
    path('permissions/', PermissionListCreateAPIView.as_view(),
         name='permission-list'),
    path('permissions/<int:pk>/',
         PermissionRetrieveUpdateDestroyAPIView.as_view(), name='permission-detail'),
    path('users/<int:pk>/assign-group/',
         UserAssignGroupView.as_view(), name='user-assign-group'),
    path('users/<int:pk>/assign-permission/',
         UserAssignPermissionView.as_view(), name='user-assign-permission'),
]
