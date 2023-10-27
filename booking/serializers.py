from rest_framework import serializers
from .models import Booking, Token,PlotResale
from plots.models import Plots
from payments.models import IncomingFund
from django.db.models import Sum


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
        booking = Booking.objects.create(**validated_data)
        return booking

    def update(self, instance, validated_data):
        booking_status = validated_data.get('status', instance.status)
        total_amount = validated_data.get(
            'total_amount', instance.total_amount)
        advance_amount = validated_data.get('advance', instance.advance)

        payments = IncomingFund.objects.filter(
            booking=instance.id).aggregate(Sum('amount'))['amount__sum'] or 0

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if booking_status == 'resale':
            plot = instance.plot
            plot.status = 'active'
            plot.save()

        instance.status = booking_status
        instance.total_receiving_amount = payments + advance_amount
        instance.remaining = total_amount-(payments + advance_amount)
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
