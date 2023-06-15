from rest_framework import serializers
from .models import Plots
from booking.models import Booking


class PlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)

    def get_plot_size(self, instance):
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    class Meta:
        model = Plots
        fields = '__all__'  # or specify specific fields


class BookingDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField(read_only=True)

    def get_customer_name(self, instance):
        name = instance.customer.name
        father_name = instance.customer.father_name
        return f"{name} || {father_name}"

    class Meta:
        model = Booking
        fields = ['customer_name', 'booking_date',
                  'total_receiving_amount', 'status']


class ResalePlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)
    booking_count = serializers.SerializerMethodField(read_only=True)
    booking_details = BookingDetailSerializer(many=True)

    def get_plot_size(self, instance):
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    def get_booking_count(self, instance):
        return instance.booking_count

    class Meta:
        model = Plots
        fields = ['id', 'plot_number', 'category_name', 'plot_size', 'address',
                  'booking_count', 'booking_details']
