from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Projects,ProjectsBalanceSheet


class ProjectsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Projects
        fields = '__all__'  # or specify specific fields


class ProjectsBalanceSheetSerializer(serializers.ModelSerializer):
    project_name=serializers.CharField(source="project.name",read_only=True)

    
    class Meta:
        model = ProjectsBalanceSheet
        fields = '__all__'  # or specify specific fields
    def to_internal_value(self, data):
        # Include 'id' field in the validated_data
        validated_data = super().to_internal_value(data)
        validated_data['id'] = data.get('id')
        return validated_data