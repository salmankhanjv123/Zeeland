from rest_framework import serializers
from .models import Customers,CustomerMessages, CustomerMessagesDocuments,CustomerMessagesReminder
from booking.models import Booking

class CustomersSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customers
        fields = '__all__'  # or specify specific fields

class CustomerMessagesReminderSerializer(serializers.ModelSerializer):
    customer_name=serializers.CharField(source="message.booking.customer.name",read_only=True)
    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_plot_info(self, instance):
        booking = instance.message.booking
        if booking:
            plot = booking.plot
            plot_number = plot.plot_number
            plot_size = plot.get_plot_size()
            plot_type = plot.get_type_display()
            return f"{plot_number} || {plot_type} || {plot_size}"
        return None
    
    class Meta:
        model = CustomerMessagesReminder
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
    username=serializers.CharField(source='user.username', read_only=True)
    booking_details = serializers.SerializerMethodField(read_only=True)


    def get_booking_details(self, instance):
        if instance.booking:
            return f"{instance.booking.booking_id} || {instance.booking.customer.name} ||  {instance.booking.plot.plot_number} -- {instance.booking.plot.get_plot_size()}"
        else:
            return "Booking details not available."
    class Meta:
        model = CustomerMessages
        fields = '__all__'

    def create(self, validated_data):
        files_data = validated_data.pop('files')
        date=validated_data.get("date")
        follow_up_message=validated_data.get("follow_up_message")
        customer_message = CustomerMessages.objects.create(**validated_data)
        for file_data in files_data:
            CustomerMessagesDocuments.objects.create(message=customer_message, **file_data)
        CustomerMessagesReminder.objects.create(message=customer_message,date=date,follow_up_message=follow_up_message)
        return customer_message

    def update(self, instance, validated_data):
        files_data = validated_data.pop('files',[])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
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
