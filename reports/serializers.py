from rest_framework import serializers
from payments.models import IncomingFund, OutgoingFund, JournalVoucher


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
