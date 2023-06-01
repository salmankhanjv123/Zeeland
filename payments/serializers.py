from rest_framework import serializers
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


class IncomingFundSerializer(serializers.ModelSerializer):
    installement_month = MonthField()
    booking_info = serializers.SerializerMethodField(read_only=True)

    def get_booking_info(self, instance):
        booking_id = instance.booking.booking_id
        customer_name = instance.booking.customer.name
        plot_number = instance.booking.plot.plot_number
        return f"{booking_id} || {customer_name} || {plot_number}"

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
