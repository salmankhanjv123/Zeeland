from rest_framework import serializers
from .models import Booking, BookingDocuments, Token, PlotResale, TokenDocuments
from plots.models import Plots
from payments.models import IncomingFund
from customer.serializers import CustomersSerializer
from plots.serializers import PlotsSerializer
from django.db.models import Sum,Q
import datetime


class PlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)

    def get_plot_size(self, instance):
        # Update this method according to your requirement
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    class Meta:
        model = Plots
        fields = "__all__"  # or specify specific fields


class BookingDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingDocuments
        exclude = ["booking"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class BookingSerializer(serializers.ModelSerializer):
    customer_info = CustomersSerializer(source="customer", read_only=True)
    dealer_name = serializers.CharField(source="dealer.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    plot_info = PlotsSerializer(source="plot", read_only=True)
    files = BookingDocumentsSerializer(many=True, required=False)

    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["total_receiving_amount"]

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        project = validated_data.get("project")
        advance_amount = validated_data.get("advance")
        total_amount = validated_data.get("total_amount")
        booking_date = validated_data.get("booking_date")
        bank = validated_data.get("bank")
        payment_type = validated_data.get("payment_type")
        cheque_number = validated_data.get("cheque_number")
        installement_month = datetime.datetime(
            booking_date.year, booking_date.month, 1
        ).date()
        try:
            latest_booking = Booking.objects.filter(project=project).latest(
                "created_at"
            )
            latest_booking_number = int(latest_booking.booking_id.split("-")[1]) + 1
        except:
            latest_booking_number = 1

        booking_id_str = str(project.id) + "-" + str(latest_booking_number).zfill(3)
        validated_data["booking_id"] = booking_id_str
        validated_data["total_receiving_amount"] = advance_amount

        plot = validated_data["plot"]
        plot.status = "sold"
        plot.save()

        existing_resale = PlotResale.objects.filter(
            Q(booking__plot=plot) | Q(booking__plot=plot.parent_plot)
        ).last()
        booking = Booking.objects.create(**validated_data)
        if booking:
            IncomingFund.objects.create(
                project=project,
                booking=booking,
                date=booking_date,
                installement_month=installement_month,
                amount=advance_amount,
                remarks="advance",
                advance_payment=True,
                bank=bank,
                payment_type=payment_type,
                cheque_number=cheque_number,
            )
        if existing_resale:
            existing_resale.company_profit=(existing_resale.remaining+existing_resale.company_amount_paid)
        for file_data in files_data:
            BookingDocuments.objects.create(booking=booking, **file_data)
        return booking

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        booking_status = validated_data.get("status", instance.status)
        total_amount = validated_data.get("total_amount", instance.total_amount)
        advance_amount = validated_data.get("advance", instance.advance)
        advance_payment_obj = IncomingFund.objects.filter(
            booking=instance, advance_payment=True
        ).first()
        if advance_payment_obj:
            advance_payment_obj.amount = advance_amount
            advance_payment_obj.save()
        payments = (
            IncomingFund.objects.filter(booking=instance.id).aggregate(Sum("amount"))[
                "amount__sum"
            ]
            or 0
        )

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if booking_status == "resale" or booking_status == "close":
            plot = instance.plot
            plot.status = "active"
            plot.save()

        instance.status = booking_status
        instance.total_receiving_amount = payments
        instance.remaining = total_amount - payments
        instance.save()

        for file_data in files_data:
            file_id = file_data.get("id", None)
            if file_id:
                file = BookingDocuments.objects.get(id=file_id, booking=instance)
                file.description = file_data.get("description", file.description)
                file.type = file_data.get("type", file.type)
                if "file" in file_data:
                    file.file = file_data.get("file", file.file)
                file.save()
            else:
                BookingDocuments.objects.create(booking=instance, **file_data)

        return instance


class BookingForPaymentsSerializer(serializers.ModelSerializer):

    booking_details = serializers.SerializerMethodField(read_only=True)

    def get_booking_details(self, instance):

        return f"{instance.booking_id} || {instance.customer.name} ||  {instance.plot.plot_number} -- {instance.plot.get_plot_size()}"

    class Meta:
        model = Booking
        fields = ["id", "booking_details","total_amount","total_receiving_amount","remaining"]


class TokenDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenDocuments
        exclude = ["token"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class TokenSerializer(serializers.ModelSerializer):
    customer_info = CustomersSerializer(source="customer", read_only=True)
    plot_info = PlotsSerializer(source="plot", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    files = TokenDocumentsSerializer(many=True, required=False)


    def get_plot_info(self, instance):
        plot_number = instance.plot.plot_number
        plot_size = instance.plot.get_plot_size()
        plot_type = instance.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"

    class Meta:
        model = Token
        fields = "__all__"

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])

        token = Token.objects.create(**validated_data)
        for file_data in files_data:
            TokenDocuments.objects.create(token=token, **file_data)
        return token

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        for file_data in files_data:
            file_id = file_data.get("id", None)
            if file_id:
                file = TokenDocuments.objects.get(id=file_id, token=instance)
                file.description = file_data.get("description", file.description)
                file.type = file_data.get("type", file.type)
                if "file" in file_data:
                    file.file = file_data.get("file", file.file)
                file.save()
            else:
                TokenDocuments.objects.create(token=instance, **file_data)

        return instance


class PlotResaleSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="booking.customer.name", read_only=True)
    booking_number = serializers.CharField(source="booking.booking_id", read_only=True)
    total_amount = serializers.FloatField(source="booking.total_amount", read_only=True)
    amount_received = serializers.FloatField(
        source="booking.total_receiving_amount", read_only=True
    )
    remaining = serializers.FloatField(source="booking.remaining", read_only=True)

    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_plot_info(self, instance):
        plot_number = instance.booking.plot.plot_number
        plot_size = instance.booking.plot.get_plot_size()
        plot_type = instance.booking.plot.get_type_display()
        return f"{plot_number} || {plot_type} || {plot_size}"

    class Meta:
        model = PlotResale
        fields = "__all__"


    def create(self, validated_data):
        booking_instance = validated_data.get('booking')
        if booking_instance:
            booking_instance.status = "close"
            booking_instance.plot.status="active"
            booking_instance.plot.save()
            booking_instance.save()
        return PlotResale.objects.create(**validated_data)