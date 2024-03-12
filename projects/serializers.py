from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Projects,BalanceSheet,BalanceSheetDetails,BalanceSheetAmountDetails


class ProjectsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Projects
        fields = '__all__'  # or specify specific fields

class BalanceSheetAmountDetailsSerializer(serializers.ModelSerializer):
    project_name=serializers.CharField(source="project.name",read_only=True)
    class Meta:
        model = BalanceSheetAmountDetails
        exclude=["detail"]  # or specify specific fields
        
    def to_internal_value(self, data):
        # Include 'id' field in the validated_data
        validated_data = super().to_internal_value(data)
        validated_data['id'] = data.get('id')
        return validated_data

class BalanceSheetDetailsSerializer(serializers.ModelSerializer):
    amount_details=BalanceSheetAmountDetailsSerializer(many=True)
    
    class Meta:
        model = BalanceSheetDetails
        exclude=["balance_sheet"]  # or specify specific fields
        
    def to_internal_value(self, data):
        # Include 'id' field in the validated_data
        validated_data = super().to_internal_value(data)
        validated_data['id'] = data.get('id')
        return validated_data

class BalanceSheetSerializer(serializers.ModelSerializer):
    details = BalanceSheetDetailsSerializer(many=True)
   
    class Meta:
        model = BalanceSheet
        fields = '__all__'  # or specify specific fields

    def to_internal_value(self, data):
        # Include 'id' field in the validated_data
        validated_data = super().to_internal_value(data)
        validated_data['id'] = data.get('id')
        return validated_data
    
    def create(self, validated_data):
        details_data = validated_data.pop('details')
        balance_sheet = BalanceSheet.objects.create(**validated_data)
        for detail_data in details_data:
            amount_details_data = detail_data.pop('amount_details')
            balance_sheet_detail = BalanceSheetDetails.objects.create(balance_sheet=balance_sheet, **detail_data)
            for amount_detail_data in amount_details_data:
                BalanceSheetAmountDetails.objects.create(detail=balance_sheet_detail, **amount_detail_data)
        return balance_sheet
