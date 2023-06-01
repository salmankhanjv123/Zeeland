from rest_framework import serializers
from .models import Booking
from plots.models import Plots


class PlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)

    def get_plot_size(self, instance):
        size_type_name = instance.get_size_type_display()
        return f"{instance.size} {size_type_name}"

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    class Meta:
        model = Plots
        fields = '__all__'  # or specify specific fields


class BookingSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField(read_only=True)
    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_customer_name(self, instance):
        return instance.customer.name

    def get_plot_info(self, instance):
        plot_number = instance.plot.plot_number
        plot_size = instance.plot.size
        size_type = instance.plot.get_size_type_display()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size} {size_type}"

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['total_remaining_amount', 'total_receiving_amount']

    def create(self, validated_data):
        project = validated_data.get('project')
        advance_amount = validated_data.get('advance')
        remaining_amount = validated_data.get('remaining')
        try:
            latest_booking = Booking.objects.filter(
                project=project).latest('created_at')
            latest_booking_number = int(
                latest_booking.booking_id.split('-')[1]) + 1
        except:
            latest_booking_number = 1

        booking_id_str = str(project.id) + \
            '-' + str(latest_booking_number).zfill(3)
        validated_data['booking_id'] = booking_id_str

        validated_data['total_receiving_amount'] = advance_amount
        validated_data['total_remaining_amount'] = remaining_amount

        booking = Booking.objects.create(**validated_data)
        return booking


class BookingForPaymentsSerializer(serializers.ModelSerializer):

    booking_details = serializers.SerializerMethodField(read_only=True)

    def get_booking_details(self, instance):
        return f"{instance['booking_id']} || {instance['customer__name']} ||  {instance['plot__plot_number']}"

    class Meta:
        model = Booking
        fields = ['id', 'booking_details']
