from rest_framework import serializers
from payments.models import IncomingFund, OutgoingFund, JournalVoucher
from rest_framework.exceptions import ValidationError
from plots.models import Plots


class IncomingFundReportSerializer(serializers.ModelSerializer):
    customer = serializers.SerializerMethodField(read_only=True)
    plot = serializers.SerializerMethodField(read_only=True)

    def get_customer(self, instance):
        return instance.booking.customer.name

    def get_plot(self, instance):
        plot = instance.booking.plot
        return f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"

    class Meta:
        model = IncomingFund
        fields = ['project', 'customer', 'plot', 'date',
                  'installement_month', 'amount', 'remarks']
        read_only_fields = fields


class OutgoingFundReportSerializer(serializers.ModelSerializer):
    expense_type = serializers.CharField(
        source='expense_type.name', read_only=True)

    class Meta:
        model = OutgoingFund
        fields = ['project', 'expense_type', 'date', 'amount', 'remarks']
        read_only_fields = fields


class JournalVoucherReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = JournalVoucher
        fields = ['project', 'type', 'date', 'amount', 'remarks']
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
        exclude=["parent_plot","status","project"]

