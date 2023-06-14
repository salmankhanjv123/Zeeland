# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User, Group, Permission
from projects.models import Projects
from django.contrib.auth.hashers import make_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True, 'required': False}}

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if 'password' in validated_data:
            instance.password = make_password(validated_data['password'])
            validated_data.pop('password')
        return super().update(instance, validated_data)


class ProjectsSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = Projects
        fields = ('id', 'name')


class UserProjectsSerializer(serializers.ModelSerializer):
    projects_list = ProjectsSerializer(many=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'projects_list')

    def update(self, instance, validated_data):
        projects_data = validated_data.pop('projects_list', None)
        if projects_data is not None:
            projects = [Projects.objects.get(
                id=data['id']) for data in projects_data]
            instance.projects_list.set(projects)
        return super().update(instance, validated_data)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = '__all__'
        extra_kwargs = {'name': {'required': False}}


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = '__all__'


class AssignGroupSerializer(serializers.ModelSerializer):
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(), many=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'groups']
        extra_kwargs = {'username': {'read_only': True}}


class AssignPermissionSerializer(serializers.ModelSerializer):
    user_permissions = serializers.PrimaryKeyRelatedField(
        queryset=Permission.objects.all(), many=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'user_permissions']
        extra_kwargs = {'username': {'read_only': True}}
