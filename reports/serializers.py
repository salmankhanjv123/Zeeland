from rest_framework import serializers
from payments.models import IncomingFund, OutgoingFund, JournalVoucher
from booking.models import Token
from rest_framework.exceptions import ValidationError
from plots.models import Plots


class IncomingFundReportSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField(read_only=True)
    plot = serializers.SerializerMethodField(read_only=True)

    def get_customer(self, instance):
        return instance.booking.customer.name

    def get_plot(self, instance):
        plot = instance.booking.plot
        return (
            f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
        )

    class Meta:
        model = IncomingFund
        fields = [
            "project",
            "customer",
            "plot",
            "date",
            "installement_month",
            "amount",
            "remarks",
        ]
        read_only_fields = fields


class OutgoingFundReportSerializer(serializers.ModelSerializer):
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    reference=serializers.SerializerMethodField(read_only=True)

    def get_reference(self, instance):
        return "expense"
    
    class Meta:
        model = OutgoingFund
        fields = "__all__"
        


class JournalVoucherReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalVoucher
        fields = ["project", "type", "date", "amount", "remarks"]
        read_only_fields = fields


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
        exclude = ["parent_plot", "status", "project"]


class BookingPaymentsSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="booking.customer.name", read_only=True
    )
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    plot = serializers.SerializerMethodField(read_only=True)

    def get_plot(self, instance):
        plots = instance.booking.plots.all()
        plot_info = [
            f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
            for plot in plots
        ]
        return plot_info

    class Meta:
        model = IncomingFund
        fields ="__all__"


class TokenPaymentsSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(
        source="customer.name", read_only=True
    )
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    plot = serializers.SerializerMethodField(read_only=True)
    reference=serializers.SerializerMethodField(read_only=True)

    def get_plot(self, instance):
        plots = instance.plot.all()
        plot_info = [
            f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
            for plot in plots
        ]
        return plot_info

    def get_reference(self, instance):
        return "token"


    class Meta:
        model = Token
        fields ="__all__"