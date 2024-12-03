from rest_framework import serializers
from django.db import transaction
from .models import Booking, BookingDocuments, Token, PlotResale, TokenDocuments
from plots.models import Plots
from payments.models import IncomingFund, Bank, BankTransaction
from customer.serializers import CustomersInfoSerializer
from plots.serializers import PlotsSerializer
from django.db.models import Sum, Q, Case, Value, F, When, FloatField
import datetime


class PlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)
    block_name=serializers.CharField(source="block.name",read_only=True)

    def get_plot_size(self, instance):
        # Update this method according to your requirement
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    class Meta:
        model = Plots
        fields = "__all__"  # or specify specific fields


class CreatePlotsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plots
        fields = ["id"]  # or specify specific fields

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class BookingDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingDocuments
        exclude = ["booking"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class BookingSerializer(serializers.ModelSerializer):
    customer_info = CustomersInfoSerializer(source="customer", read_only=True)
    dealer_name = serializers.CharField(source="dealer.name", read_only=True)
    bank_name = serializers.CharField(source="bank.name", read_only=True)
    plot_info = PlotsSerializer(source="plots", many=True, read_only=True)
    files = BookingDocumentsSerializer(many=True, required=False)
    plots = CreatePlotsSerializer(many=True)

    class Meta:
        model = Booking
        fields = "__all__"
        read_only_fields = ["total_receiving_amount"]

    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        plots_data = validated_data.pop("plots", [])
        advance_amount = validated_data.get("advance", 0)
        project = validated_data.get("project")
        token = validated_data.get("token")
        booking_date = validated_data.get("booking_date")
        installement_month = datetime.datetime(
            booking_date.year, booking_date.month, 1
        ).date()

        try:
            with transaction.atomic():
                try:
                    latest_booking = Booking.objects.filter(project=project).latest(
                        "created_at"
                    )
                    latest_booking_number = int(latest_booking.booking_id.split("-")[1]) + 1
                except Booking.DoesNotExist:
                    latest_booking_number = 1

                booking_id_str = f"{project.id}-{str(latest_booking_number).zfill(3)}"
                validated_data["booking_id"] = booking_id_str
                token_amount = token.amount if token else 0
                validated_data["total_receiving_amount"] = advance_amount + token_amount

                if token:
                    token.status = "accepted"
                    token.save()

                booking = Booking.objects.create(**validated_data)

                if plots_data:
                    booking.plots.set([plot["id"] for plot in plots_data])
                    # for plot_data in plots_data:
                    #     plot_id = plot_data["id"]
                    #     plot = Plots.objects.get(id=plot_id)
                    #     plot.status = "sold"
                    #     plot.save()

                for file_data in files_data:
                    BookingDocuments.objects.create(booking=booking, **file_data)

                if advance_amount > 0:
                    
                    try:
                        latest_payment = IncomingFund.objects.filter(project=project).latest(
                            "created_at"
                        )
                        latest_payment_number = int(latest_payment.document_number) + 1
                    except IncomingFund.DoesNotExist:
                        latest_payment_number = 1
                    document_number_str = str(latest_payment_number).zfill(3)
                    
                    IncomingFund.objects.create(
                        project=project,
                        booking=booking,
                        document_number=document_number_str,
                        date=booking_date,
                        installement_month=installement_month,
                        amount=advance_amount,
                        remarks="advance",
                        advance_payment=True,
                        bank=validated_data.get("bank"),
                        payment_type=validated_data.get("payment_type"),
                        cheque_number=validated_data.get("cheque_number"),
                    )
                self.create_bank_transactions(booking, validated_data)
                return booking
        except Exception as e:
            raise serializers.ValidationError(f"Error creating booking: {e}")

    def create_bank_transactions(self, booking, validated_data):
        """Create multiple bank transactions for different accounts."""
        project = validated_data.get("project")
        booking_date = validated_data.get("booking_date")
        booking_amount = validated_data.get("total_amount", 0)
        advance_amount = validated_data.get("advance", 0)
        dealer_comission_amount = validated_data.get("dealer_comission_amount", 0)
        plot_cost = sum(plot.cost_price for plot in booking.plots.all())

        advance_bank = validated_data.get("bank")
        payment_type = validated_data.get("payment_type")
        is_deposit = advance_bank.detail_type != "Undeposited_Funds"
        is_cheque_clear = payment_type != "Cheque"

        # Account receivable (Debit)
        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()
        if account_receivable_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_receivable_bank,
                transaction_type="Booking",
                payment=0,
                deposit=booking_amount,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

        # Sale account (Credit)
        sale_bank = Bank.objects.filter(
            used_for="Sale_Account", project=project
        ).first()
        if sale_bank:
            BankTransaction.objects.create(
                project=project,
                bank=sale_bank,
                transaction_type="Booking",
                deposit=booking_amount,
                payment=0,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

        # Cost of Goods Sold (COGS - Debit)
        cogs_bank = Bank.objects.filter(
            used_for="Cost_of_Good_Sold", project=project
        ).first()
        if cogs_bank:
            BankTransaction.objects.create(
                project=project,
                bank=cogs_bank,
                transaction_type="Booking",
                payment=0,
                deposit=plot_cost,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

        # Land Inventory (Credit)
        land_inventory_bank = Bank.objects.filter(
            used_for="Land_Inventory", project=project
        ).first()
        if land_inventory_bank:
            BankTransaction.objects.create(
                project=project,
                bank=land_inventory_bank,
                transaction_type="Booking",
                deposit=0,
                payment=plot_cost,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

        # Advance payment (credit - account receivable) (debit - bank)
        if advance_amount > 0 and account_receivable_bank and advance_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_receivable_bank,
                transaction_type="Booking_Advance",
                payment=advance_amount,
                deposit=0,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

            BankTransaction.objects.create(
                project=project,
                bank=advance_bank,
                transaction_type="Booking_Advance",
                payment=0,
                deposit=advance_amount,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
                is_deposit=is_deposit,
                is_cheque_clear=is_cheque_clear,
            )

        # Dealer Comission (credit - account payable) (debit - dealer expense)
        account_payable_bank = Bank.objects.filter(
            used_for="Account_Payable", project=project
        ).first()
        dealer_expense_bank = Bank.objects.filter(
            used_for="Dealer_Expense", project=project
        ).first()
        if dealer_comission_amount > 0 and account_payable_bank and dealer_expense_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_payable_bank,
                transaction_type="Dealer_Comission",
                payment=0,
                deposit=dealer_comission_amount,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

            BankTransaction.objects.create(
                project=project,
                bank=dealer_expense_bank,
                transaction_type="Dealer_Comission",
                payment=0,
                deposit=dealer_comission_amount,
                transaction_date=booking_date,
                related_table="Booking",
                related_id=booking.id,
            )

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        plots_data = validated_data.pop("plots", [])
        token = validated_data.get("token", instance.token)
        project= validated_data.get("project", instance.project)
        token_amount = token.amount if token else 0
        booking_date = validated_data.get("booking_date", instance.booking_date)
        installement_month = datetime.datetime(
            booking_date.year, booking_date.month, 1
        ).date()

        try:
            with transaction.atomic():
                self.update_bank_transactions(instance, validated_data)
                # if instance.plots.exists():
                #     for existing_plot in instance.plots.all():
                #         existing_plot.status = "active"
                #         existing_plot.save()

                for key, value in validated_data.items():
                    setattr(instance, key, value)
                instance.save()

                if plots_data:
                    instance.plots.set([plot["id"] for plot in plots_data])
                    # for plot_data in plots_data:
                    #     plot_id = plot_data["id"]
                    #     plot = Plots.objects.get(id=plot_id)
                    #     plot.status = "sold"
                    #     plot.save()

                advance_amount = validated_data.get("advance", instance.advance)
                advance_payment_obj = IncomingFund.objects.filter(
                    booking=instance, advance_payment=True
                ).first()

                if advance_payment_obj:
                    advance_payment_obj.amount = advance_amount
                    advance_payment_obj.save()
                else:
                    # If no advance payment exists, and advance_amount > 0, create a new IncomingFund
                                        
                    try:
                        latest_payment = IncomingFund.objects.filter(project=project).latest(
                            "created_at"
                        )
                        latest_payment_number = int(latest_payment.document_number) + 1
                    except IncomingFund.DoesNotExist:
                        latest_payment_number = 1
                    document_number_str = str(latest_payment_number).zfill(3)
                    if advance_amount > 0:
                        IncomingFund.objects.create(
                            project=instance.project,
                            document_number=document_number_str,
                            booking=instance,
                            date=booking_date,
                            installement_month=installement_month,
                            amount=advance_amount,
                            remarks="advance",
                            advance_payment=True,
                            bank=validated_data.get("bank"),
                            payment_type=validated_data.get("payment_type"),
                            cheque_number=validated_data.get("cheque_number"),
                        )

                payments = (
                    IncomingFund.objects.filter(booking=instance.id).aggregate(
                        total=Sum(
                            Case(
                                When(reference="payment", then=F("amount")),
                                When(reference="return", then=F("amount") * -1),
                                default=Value(0),
                                output_field=FloatField(),
                            )
                        )
                    )["total"]
                    or 0.0
                )
                instance.total_receiving_amount = payments + token_amount
                instance.remaining = instance.total_amount - payments - token_amount
                instance.save()

                # Handle file updates and deletions
                existing_files = BookingDocuments.objects.filter(booking=instance)
                updated_file_ids = {
                    file_data.get("id") for file_data in files_data if "id" in file_data
                }

                # Delete files that are not in t  he updated files_data
                files_to_delete = existing_files.exclude(id__in=updated_file_ids)
                for file in files_to_delete:
                    file.delete()

                for file_data in files_data:
                    file_id = file_data.get("id", None)
                    if file_id:
                        file = BookingDocuments.objects.get(
                            id=file_id, booking=instance
                        )
                        file.description = file_data.get(
                            "description", file.description
                        )
                        file.type = file_data.get("type", file.type)
                        if "file" in file_data:
                            file.file = file_data.get("file", file.file)
                        file.save()
                    else:
                        BookingDocuments.objects.create(booking=instance, **file_data)

                return instance
        except Exception as e:
            raise serializers.ValidationError(f"Error updating booking: {e}")

    def update_bank_transactions(self, booking, validated_data):
        """Update bank transactions for different accounts when a booking is updated."""
        project = validated_data.get("project", booking.project)
        booking_date = validated_data.get("booking_date", booking.booking_date)
        booking_amount = validated_data.get("total_amount", booking.total_amount)
        advance_amount = validated_data.get("advance", booking.advance)
        dealer_comission_amount = validated_data.get(
            "dealer_comission_amount", booking.dealer_comission_amount
        )
        plot_cost = sum(plot.cost_price for plot in booking.plots.all())
        new_bank = validated_data.get("bank", booking.bank)


        # Account receivable (Debit)
        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()
        if account_receivable_bank:
            BankTransaction.objects.filter(
                project=project,
                bank=account_receivable_bank,
                related_table="Booking",
                related_id=booking.id,
            ).update(payment=0, deposit=booking_amount, transaction_date=booking_date)

        # Sale account (Credit)
        sale_bank = Bank.objects.filter(
            used_for="Sale_Account", project=project
        ).first()
        if sale_bank:
            BankTransaction.objects.filter(
                project=project,
                bank=sale_bank,
                related_table="Booking",
                related_id=booking.id,
            ).update(deposit=booking_amount, payment=0, transaction_date=booking_date)

        # Cost of Goods Sold (COGS - Debit)
        cogs_bank = Bank.objects.filter(
            used_for="Cost_of_Good_Sold", project=project
        ).first()
        if cogs_bank:
            BankTransaction.objects.filter(
                project=project,
                bank=cogs_bank,
                related_table="Booking",
                related_id=booking.id,
            ).update(payment=0, deposit=plot_cost, transaction_date=booking_date)

        # Land Inventory (Credit)
        land_inventory_bank = Bank.objects.filter(
            used_for="Land_Inventory", project=project
        ).first()
        if land_inventory_bank:
            BankTransaction.objects.filter(
                project=project,
                bank=land_inventory_bank,
                related_table="Booking",
                related_id=booking.id,
            ).update(deposit=0, payment=plot_cost, transaction_date=booking_date)

        # Advance payment (Credit - Account Receivable) (Debit - Bank)
        if advance_amount > 0 and account_receivable_bank and new_bank:
            BankTransaction.objects.filter(
                project=project,
                bank=account_receivable_bank,
                transaction_type="Booking_Advance",
                related_table="Booking",
                related_id=booking.id,
            ).update(payment=advance_amount, deposit=0, transaction_date=booking_date)

        # Retrieve the existing transaction to use its current `is_deposit` value if no bank change
            existing_transaction = BankTransaction.objects.filter(
                project=project,
                bank=booking.bank,
                related_table="Booking",
                related_id=booking.id,
            ).first()

            # Default to the existing is_deposit value if the bank hasn't changed
            is_deposit = existing_transaction.is_deposit if existing_transaction else True
            bank_changed = booking.bank != new_bank

            # Update is_deposit based on the change in bank detail type
            if bank_changed:
                if new_bank.detail_type != "Undeposited_Funds":
                    is_deposit = True
                elif booking.bank.detail_type != "Undeposited_Funds" and new_bank.detail_type == "Undeposited_Funds":
                    is_deposit = False
            
            BankTransaction.objects.filter(
                project=project,
                bank=booking.bank,
                transaction_type="Booking_Advance",
                related_table="Booking",
                related_id=booking.id,
            ).update(
                payment=0,
                bank=new_bank,
                deposit=advance_amount,
                transaction_date=booking_date,
                is_deposit=is_deposit,
            )

        # Dealer Comission (Credit - Account Payable) (Debit - Dealer Expense)
        account_payable_bank = Bank.objects.filter(
            used_for="Account_Payable", project=project
        ).first()
        dealer_expense_bank = Bank.objects.filter(
            used_for="Dealer_Expense", project=project
        ).first()
        if dealer_comission_amount > 0 and account_payable_bank and dealer_expense_bank:
            # Update or create transaction for account payable bank
            BankTransaction.objects.update_or_create(
                project=project,
                bank=account_payable_bank,
                transaction_type="Dealer_Comission",
                related_table="Booking",
                related_id=booking.id,
                defaults={
                    "payment": 0,
                    "deposit": dealer_comission_amount,
                    "transaction_date": booking_date,
                }
            )

            # Update or create transaction for dealer expense bank
            BankTransaction.objects.update_or_create(
                project=project,
                bank=dealer_expense_bank,
                transaction_type="Dealer_Comission",
                related_table="Booking",
                related_id=booking.id,
                defaults={
                    "payment": 0,
                    "deposit": dealer_comission_amount,
                    "transaction_date": booking_date,
                }
            )


class BookingForPaymentsSerializer(serializers.ModelSerializer):

    booking_details = serializers.SerializerMethodField(read_only=True)
    dealer_details = serializers.SerializerMethodField(read_only=True)

    def get_booking_details(self, instance):

        return f"{instance.booking_id} || {instance.customer.name}"

    def get_dealer_details(self, instance):
        dealer = instance.dealer
        if dealer:
            return f"{instance.booking_id} || {dealer.name}"
        else:
            return None

    class Meta:
        model = Booking
        fields = [
            "id",
            "booking_details",
            "dealer_details",
            "total_amount",
            "total_receiving_amount",
            "remaining",
        ]


class TokenDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TokenDocuments
        exclude = ["token"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data


class TokenSerializer(serializers.ModelSerializer):
    customer_info = CustomersInfoSerializer(source="customer", read_only=True)
    plot_info = PlotsSerializer(source="plot", many=True, read_only=True)
    plot = CreatePlotsSerializer(many=True)
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
    
    @transaction.atomic
    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        plots_data = validated_data.pop("plot", [])
        project=validated_data.get("project")
        
        try:
            latest_token = Token.objects.filter(project=project).latest(
                "created_at"
            )
            latest_token_number = int(latest_token.document_number) + 1
        except Token.DoesNotExist:
            latest_token_number = 1

        document_number_str = str(latest_token_number).zfill(3)
        validated_data["document_number"] = document_number_str
        
        token = Token.objects.create(**validated_data)

        if plots_data:
            token.plot.set([plot["id"] for plot in plots_data])

        for file_data in files_data:
            TokenDocuments.objects.create(token=token, **file_data)
        self.create_bank_transactions(token, validated_data)
        return token

    def create_bank_transactions(self, payment, validated_data):
        """Create multiple bank transactions for different accounts."""
        project = validated_data.get("project")
        date = validated_data.get("date")
        amount = validated_data.get("amount", 0)
        bank = validated_data.get("bank")
        payment_type = validated_data.get("payment_type")
        is_deposit = bank.detail_type != "Undeposited_Funds"
        is_cheque_clear = payment_type != "Cheque"

        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()

        BankTransaction.objects.create(
            project=project,
            bank=account_receivable_bank,
            transaction_type="Token",
            payment=amount,
            deposit=0,
            transaction_date=date,
            related_table="token",
            related_id=payment.id,
        )

        BankTransaction.objects.create(
            project=project,
            bank=bank,
            transaction_type="Token",
            payment=0,
            deposit=amount,
            transaction_date=date,
            related_table="token",
            related_id=payment.id,
            is_deposit=is_deposit,
            is_cheque_clear=is_cheque_clear,
        )

    @transaction.atomic
    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        plots_data = validated_data.pop("plot", [])
        self.update_bank_transactions(instance, validated_data)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()

        if plots_data:
            instance.plot.set([plot["id"] for plot in plots_data])
        # Handle file updates and deletions
        existing_files = TokenDocuments.objects.filter(token=instance)
        updated_file_ids = {
            file_data.get("id") for file_data in files_data if "id" in file_data
        }

        # Delete files that are not in t  he updated files_data
        files_to_delete = existing_files.exclude(id__in=updated_file_ids)
        for file in files_to_delete:
            file.delete()

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

    def update_bank_transactions(self, payment, validated_data):
        """Update bank transactions for the given payment."""
        project = validated_data.get("project", payment.project)
        date = validated_data.get("date", payment.date)
        amount = validated_data.get("amount", payment.amount)
        new_bank = validated_data.get("bank", payment.bank)


        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()

        BankTransaction.objects.filter(
            project=project,
            bank=account_receivable_bank,
            transaction_type="Token",
            related_table="token",
            related_id=payment.id,
        ).update(
            payment=amount,
            deposit=0,
            transaction_date=date,
        )

        # Retrieve the existing transaction to use its current `is_deposit` value if no bank change
        existing_transaction = BankTransaction.objects.filter(
            project=project,
            bank=payment.bank,
            related_table="token",
            related_id=payment.id,
        ).first()

        # Default to the existing is_deposit value if the bank hasn't changed
        is_deposit = existing_transaction.is_deposit if existing_transaction else True
        bank_changed = payment.bank != new_bank

        # Update is_deposit based on the change in bank detail type
        if bank_changed:
            if new_bank.detail_type != "Undeposited_Funds":
                is_deposit = True
            elif payment.bank.detail_type != "Undeposited_Funds" and new_bank.detail_type == "Undeposited_Funds":
                is_deposit = False
       
        # Update transaction for the specified bank
        BankTransaction.objects.filter(
            project=project,
            bank=payment.bank,
            transaction_type="Token",
            related_table="token",
            related_id=payment.id,
        ).update(
            bank=new_bank,
            payment=0,
            deposit=amount,
            transaction_date=date,
            is_deposit=is_deposit,
        )


class PlotResaleSerializer(serializers.ModelSerializer):
    customer = serializers.CharField(source="booking.customer.name", read_only=True)
    booking_number = serializers.CharField(source="booking.booking_id", read_only=True)
    total_amount = serializers.FloatField(source="booking.total_amount", read_only=True)

    plot_info = serializers.SerializerMethodField(read_only=True)

    def get_plot_info(self, instance):
        plots = instance.booking.plots.all()
        plot_info = [
            f"{plot.plot_number} || {plot.get_type_display()} || {plot.get_plot_size()}"
            for plot in plots
        ]
        return plot_info

    class Meta:
        model = PlotResale
        fields = "__all__"

    @transaction.atomic
    def create(self, validated_data):
        booking = validated_data.get("booking")
        booking.status = "close"
        booking.save()

        plots = booking.plots.all()
        for plot in plots:
            plot.status = "active"
            plot.save()

        plot_resale = PlotResale.objects.create(**validated_data)
        self.create_bank_transactions(plot_resale, validated_data)
        return plot_resale

    def create_bank_transactions(self, plot_resale, validated_data):
        """Create multiple bank transactions for different accounts."""
        project = plot_resale.booking.project
        date = validated_data.get("date")
        remaining = validated_data.get("remaining")
        company_amount_paid = validated_data.get("company_amount_paid")
        amount_received = validated_data.get("amount_received")
        plot_cost = sum(plot.cost_price for plot in plot_resale.booking.plots.all())
        booking_amount = plot_resale.booking.total_amount

        if company_amount_paid > amount_received:
            extra_refund_expense = Bank.objects.filter(
                used_for="Extra_Refund_Expense", project=project
            ).first()
            BankTransaction.objects.create(
                project=project,
                bank=extra_refund_expense,
                transaction_type="Close_Booking",
                payment=0,
                deposit=company_amount_paid - amount_received,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )
        elif company_amount_paid < amount_received:
            extra_refund_income = Bank.objects.filter(
                used_for="Extra_Refund_Income", project=project
            ).first()
            BankTransaction.objects.create(
                project=project,
                bank=extra_refund_income,
                transaction_type="Close_Booking",
                payment=0,
                deposit=amount_received - company_amount_paid,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Account Payable (credit)
        account_payable_bank = Bank.objects.filter(
            used_for="Account_Payable", project=project
        ).first()
        if account_payable_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_payable_bank,
                transaction_type="Close_Booking",
                payment=0,
                deposit=company_amount_paid,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Account receivable (credit)
        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()
        if account_receivable_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_receivable_bank,
                transaction_type="Close_Booking",
                payment=remaining,
                deposit=0,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Sale account (debit with booking price)
        sale_bank = Bank.objects.filter(
            used_for="Sale_Account", project=project
        ).first()
        if sale_bank:
            BankTransaction.objects.create(
                project=project,
                bank=sale_bank,
                transaction_type="Close_Booking",
                deposit=0,
                payment=booking_amount,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Cost of Goods Sold (COGS - credit)
        cogs_bank = Bank.objects.filter(
            used_for="Cost_of_Good_Sold", project=project
        ).first()
        if cogs_bank:
            BankTransaction.objects.create(
                project=project,
                bank=cogs_bank,
                transaction_type="Close_Booking",
                payment=plot_cost,
                deposit=0,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Land Inventory (debit)
        land_inventory_bank = Bank.objects.filter(
            used_for="Land_Inventory", project=project
        ).first()
        if land_inventory_bank:
            BankTransaction.objects.create(
                project=project,
                bank=land_inventory_bank,
                transaction_type="Close_Booking",
                deposit=plot_cost,
                payment=0,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

    @transaction.atomic
    def update(self, instance, validated_data):
        self.update_bank_transactions(instance, validated_data)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        return instance

    def update_bank_transactions(self, plot_resale, validated_data):
        BankTransaction.objects.filter(related_id=plot_resale.id).delete()
        
        project = plot_resale.booking.project
        date = validated_data.get("date")
        remaining = validated_data.get("remaining")
        company_amount_paid = validated_data.get("company_amount_paid")
        amount_received = validated_data.get("amount_received")
        plot_cost = sum(plot.cost_price for plot in plot_resale.booking.plots.all())
        booking_amount = plot_resale.booking.total_amount

        if company_amount_paid > amount_received:
            extra_refund_expense = Bank.objects.filter(
                used_for="Extra_Refund_Expense", project=project
            ).first()
            BankTransaction.objects.create(
                project=project,
                bank=extra_refund_expense,
                transaction_type="Close_Booking",
                payment=0,
                deposit=company_amount_paid - amount_received,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )
        elif company_amount_paid < amount_received:
            extra_refund_income = Bank.objects.filter(
                used_for="Extra_Refund_Income", project=project
            ).first()
            BankTransaction.objects.create(
                project=project,
                bank=extra_refund_income,
                transaction_type="Close_Booking",
                payment=0,
                deposit=amount_received - company_amount_paid,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Account Payable (credit)
        account_payable_bank = Bank.objects.filter(
            used_for="Account_Payable", project=project
        ).first()
        if account_payable_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_payable_bank,
                transaction_type="Close_Booking",
                payment=0,
                deposit=company_amount_paid,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Account receivable (credit)
        account_receivable_bank = Bank.objects.filter(
            used_for="Account_Receivable", project=project
        ).first()
        if account_receivable_bank:
            BankTransaction.objects.create(
                project=project,
                bank=account_receivable_bank,
                transaction_type="Close_Booking",
                payment=remaining,
                deposit=0,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Sale account (debit with booking price)
        sale_bank = Bank.objects.filter(
            used_for="Sale_Account", project=project
        ).first()
        if sale_bank:
            BankTransaction.objects.create(
                project=project,
                bank=sale_bank,
                transaction_type="Close_Booking",
                deposit=0,
                payment=booking_amount,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Cost of Goods Sold (COGS - credit)
        cogs_bank = Bank.objects.filter(
            used_for="Cost_of_Good_Sold", project=project
        ).first()
        if cogs_bank:
            BankTransaction.objects.create(
                project=project,
                bank=cogs_bank,
                transaction_type="Close_Booking",
                payment=plot_cost,
                deposit=0,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )

        # Land Inventory (debit)
        land_inventory_bank = Bank.objects.filter(
            used_for="Land_Inventory", project=project
        ).first()
        if land_inventory_bank:
            BankTransaction.objects.create(
                project=project,
                bank=land_inventory_bank,
                transaction_type="Close_Booking",
                deposit=plot_cost,
                payment=0,
                transaction_date=date,
                related_table="plot_resale",
                related_id=plot_resale.id,
            )