from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from plots.models import Plots
from .models import Projects,BalanceSheet,BalanceSheetDetails,BalanceSheetAmountDetails


class ProjectsSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Projects
        fields = '__all__'  # or specify specific fields

    @transaction.atomic
    def update(self, instance, validated_data):
        # Update the instance with validated data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # Save the updated instance to persist changes
        instance.save()
        plots = Plots.objects.filter(project_id=instance.id)
        # Update cost_price for each plot
        cost_per_marla = validated_data.get("cost_per_marla", None)
        if cost_per_marla is not None:
            for plot in plots:
                plot.cost_price = cost_per_marla * plot.marlas
                plot.save()
        return instance

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

    def update(self, instance, validated_data):
        details_data = validated_data.pop('details')
        instance = super().update(instance, validated_data)
        if details_data:
            for detail_data in details_data:
                detail_instance = instance.details.filter(id=detail_data.get('id')).first()
                if detail_instance:
                    amount_details_data = detail_data.pop('amount_details')
                    for amount_detail_data in amount_details_data:
                        amount_detail_instance = detail_instance.amount_details.filter(id=amount_detail_data.get('id')).first()
                        if amount_detail_instance:
                            for key, value in amount_detail_data.items():
                                setattr(amount_detail_instance, key, value)
                            amount_detail_instance.save()
                    for key, value in detail_data.items():
                        setattr(detail_instance, key, value)
                    detail_instance.save()
        return instance