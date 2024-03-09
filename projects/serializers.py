from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Projects,ProjectsBalanceSheet,BalanceSheetDetail


class ProjectsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Projects
        fields = '__all__'  # or specify specific fields

class BalanceSheetDetailSerializer(serializers.ModelSerializer):
    project_name=serializers.CharField(source="project.name",read_only=True)
    
    class Meta:
        model = BalanceSheetDetail
        exclude=["balance_sheet"]  # or specify specific fields
        
    def to_internal_value(self, data):
        # Include 'id' field in the validated_data
        validated_data = super().to_internal_value(data)
        validated_data['id'] = data.get('id')
        return validated_data

class ProjectsBalanceSheetSerializer(serializers.ModelSerializer):
    payments_detail=BalanceSheetDetailSerializer(many=True)

    
    class Meta:
        model = ProjectsBalanceSheet
        fields = '__all__'  # or specify specific fields

    def to_internal_value(self, data):
        # Include 'id' field in the validated_data
        validated_data = super().to_internal_value(data)
        validated_data['id'] = data.get('id')
        return validated_data
    
    def create(self, validated_data):
        payments_detail_data = validated_data.pop('payments_detail', [])
        projects_balance_sheet = ProjectsBalanceSheet.objects.create(**validated_data)
        for payment_data in payments_detail_data:
            BalanceSheetDetail.objects.create(balance_sheet=projects_balance_sheet, **payment_data)
        return projects_balance_sheet

    def update(self, instance, validated_data):
        payments_detail_data = validated_data.pop('payments_detail', [])
        instance = super().update(instance, validated_data)
        existing_payments_detail = instance.payments_detail.all()
        existing_payments_detail_ids = [payment.id for payment in existing_payments_detail]
        for payment_data in payments_detail_data:
            payment_id = payment_data.get('id')
            if payment_id:
                payment = existing_payments_detail.get(id=payment_id)
                BalanceSheetDetail.objects.filter(id=payment_id).update(**payment_data)
                existing_payments_detail_ids.remove(payment_id)
            else:
                BalanceSheetDetail.objects.create(balance_sheet=instance, **payment_data)
        BalanceSheetDetail.objects.filter(id__in=existing_payments_detail_ids).delete()
        return instance