from rest_framework import serializers
from .models import Customers,CustomerMessages, CustomerMessagesDocuments
from booking.models import Booking

class CustomersSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customers
        fields = '__all__'  # or specify specific fields

class CustomerMessagesDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerMessagesDocuments
        exclude=["message"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class CustomerMessagesSerializer(serializers.ModelSerializer):
    files = CustomerMessagesDocumentsSerializer(many=True)
    customer = serializers.CharField(source='customer_name', read_only=True)

    class Meta:
        model = CustomerMessages
        fields = '__all__'

    def create(self, validated_data):
        files_data = validated_data.pop('files')
        customer_message = CustomerMessages.objects.create(**validated_data)
        for file_data in files_data:
            CustomerMessagesDocuments.objects.create(message=customer_message, **file_data)
        return customer_message

    def update(self, instance, validated_data):
        files_data = validated_data.pop('files')
        instance.date = validated_data.get('date', instance.date)
        instance.notes = validated_data.get('notes', instance.notes)
        instance.save()

        for file_data in files_data:
            file_id = file_data.get('id', None)
            if file_id:
                file = CustomerMessagesDocuments.objects.get(id=file_id, message=instance)
                file.description = file_data.get('description', file.description)
                file.type= file_data.get('type', file.type)
                if 'file' in file_data:
                    file.file = file_data.get('file', file.file)
                file.save()
            else:
                CustomerMessagesDocuments.objects.create(message=instance, **file_data)

        return instance
