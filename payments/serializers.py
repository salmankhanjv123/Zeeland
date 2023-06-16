from rest_framework import serializers
from booking.models import Booking
from customer.models import Customers
from .models import ExpenseType, IncomingFund, OutgoingFund, JournalVoucher
import datetime


class MonthField(serializers.Field):
    def to_internal_value(self, data):
        # Validate the month string and return a datetime object with day set to 1
        try:
            year, month = data.split("-")
            return datetime.datetime(int(year), int(month), 1).date()
        except (ValueError, AttributeError):
            raise serializers.ValidationError(
                "Invalid month format. Use 'YYYY-MM'.")

    def to_representation(self, value):
        # Convert the datetime object to a month string in the format 'YYYY-MM'
        if value is not None:
            return value.strftime("%Y-%m")
        return value


class BookingSerializer(serializers.ModelSerializer):
    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_plot_info(self, instance):
        plot_number = instance.plot.plot_number
        plot_size = instance.plot.get_plot_size()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"

    class Meta:
        model = Booking
        fields = ['plot_info', 'total_amount',
                  'remaining', 'total_receiving_amount']
        read_only_fields = fields


class CustomersSerializer(serializers.ModelSerializer):

    class Meta:
        model = Customers
        fields = ['name', 'father_name', 'contact', 'cnic']


class IncomingFundSerializer(serializers.ModelSerializer):
    installement_month = MonthField()
    booking_info = BookingSerializer(source='booking', read_only=True)
    customer = CustomersSerializer(source='booking.customer', read_only=True)

    def create(self, validated_data):
        booking = validated_data['booking']
        amount = validated_data['amount']

        booking.total_receiving_amount += amount
        booking.remaining -= amount
        booking.save()
        return IncomingFund.objects.create(**validated_data)

    def update(self, instance, validated_data):
        booking = instance.booking
        amount = validated_data.get('amount', instance.amount)

        if amount != instance.amount:
            booking.total_receiving_amount -= instance.amount
            booking.remaining += instance.amount
            booking.total_receiving_amount += amount
            booking.remaining -= amount
            booking.save()

        instance.amount = amount
        instance.save()
        return instance

    class Meta:
        model = IncomingFund
        fields = '__all__'


class OutgoingFundSerializer(serializers.ModelSerializer):
    expense_type_name = serializers.CharField(
        source="expense_type.name", read_only=True)

    class Meta:
        model = OutgoingFund
        fields = '__all__'


class ExpenseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExpenseType
        fields = '__all__'


class JournalVoucherSerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalVoucher
        fields = '__all__'
