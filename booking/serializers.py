from rest_framework import serializers
from .models import Booking, Token,PlotResale
from plots.models import Plots
from payments.models import IncomingFund
from django.db.models import Sum
import datetime

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
        plot_size = instance.plot.get_plot_size()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"

    class Meta:
        model = Booking
        fields = '__all__'
        read_only_fields = ['total_receiving_amount']

    def create(self, validated_data):
        project = validated_data.get('project')
        advance_amount = validated_data.get('advance')
        total_amount=validated_data.get("total_amount")
        booking_date=validated_data.get("booking_date")
        installement_month=datetime.datetime(booking_date.year, booking_date.month, 1).date()
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

        plot = validated_data['plot']
        plot.status = "sold"
        plot.save()
        existing_resale_exists = Booking.objects.filter(plot=plot, status="resale").exists()
        booking = Booking.objects.create(**validated_data)
        if booking:
            IncomingFund.objects.create(project=project,booking=booking,date=booking_date,installement_month=installement_month,amount=advance_amount,remarks="advance",advance_payment=True)
        if existing_resale_exists:
            PlotResale.objects.create(booking=booking,plot=plot,entry_type="booking",new_plot_price=total_amount)
        return booking

    def update(self, instance, validated_data):
        booking_status = validated_data.get('status', instance.status)
        total_amount = validated_data.get(
            'total_amount', instance.total_amount)
        advance_amount = validated_data.get('advance', instance.advance)
        advance_payment_obj = IncomingFund.objects.filter(booking=instance, advance_payment=True).first()
        if advance_payment_obj:
            advance_payment_obj.amount = advance_amount
            advance_payment_obj.save()
        payments = IncomingFund.objects.filter(
            booking=instance.id).aggregate(Sum('amount'))['amount__sum'] or 0

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if booking_status == 'resale' or booking_status == 'close':
            plot = instance.plot
            plot.status = 'active'
            plot.save()

        instance.status = booking_status
        instance.total_receiving_amount = payments 
        instance.remaining = total_amount-payments 
        instance.save()


        return instance


class BookingForPaymentsSerializer(serializers.ModelSerializer):

    booking_details = serializers.SerializerMethodField(read_only=True)

    def get_booking_details(self, instance):

        return f"{instance.booking_id} || {instance.customer.name} ||  {instance.plot.plot_number} -- {instance.plot.get_plot_size()}"

    class Meta:
        model = Booking
        fields = ['id', 'booking_details']


class TokenSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField(read_only=True)
    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_customer_name(self, instance):
        return instance.customer.name

    def get_plot_info(self, instance):
        plot_number = instance.plot.plot_number
        plot_size = instance.plot.get_plot_size()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"

    class Meta:
        model = Token
        fields = '__all__'



class PlotResaleSerializer(serializers.ModelSerializer):
    customer=serializers.CharField(source="booking.customer.name",read_only=True)
    booking_number=serializers.CharField(source="booking.booking_id",read_only=True)
    total_amount=serializers.FloatField(source="booking.total_amount",read_only=True)
    amount_received=serializers.FloatField(source="booking.total_receiving_amount",read_only=True)
    remaining=serializers.FloatField(source="booking.remaining",read_only=True)

    plot_info = serializers.SerializerMethodField(read_only=True)


    def get_plot_info(self, instance):
        plot_number = instance.plot.plot_number
        plot_size = instance.plot.get_plot_size()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"
    
    class Meta:
        model = PlotResale
        fields = '__all__'
