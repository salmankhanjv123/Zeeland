from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Plots,PlotsDocuments,Block
from booking.models import Booking


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__' 

class PlotsDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlotsDocuments
        exclude = ["plot"]

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["id"] = data.get("id")
        return validated_data

class SubPlotsSerializer(serializers.ModelSerializer):
    plot_size = serializers.SerializerMethodField(read_only=True)
    category_name = serializers.SerializerMethodField(read_only=True)
    def get_plot_size(self, instance):
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"
    class Meta:
        model = Plots
        fields = ['id', 'plot_number', 'address', 'type', 'marlas', 'square_fts', 'rate', 'status','plot_size','category_name']


class PlotsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField(read_only=True)
    block_name=serializers.CharField(source="block.name",read_only=True)
    plot_size = serializers.SerializerMethodField(read_only=True)
    files = PlotsDocumentsSerializer(many=True, required=False)
    sub_plots=SubPlotsSerializer(many=True,read_only=True)
    parent_plot_info=SubPlotsSerializer(source="parent_plot",read_only=True)

    def get_plot_size(self, instance):
        return instance.get_plot_size()

    def get_category_name(self, instance):
        category_name = instance.get_type_display()
        return f"{category_name}"

    class Meta:
        model = Plots
        fields = '__all__'  # or specify specific fields


    def create(self, validated_data):
        files_data = validated_data.pop("files", [])
        project = validated_data.get('project')
        project_id=project.id
        plot_number = validated_data.get('plot_number')

        if Plots.objects.filter(project=project, plot_number=plot_number).exists() and project_id!=5:
            raise ValidationError({"error": f"A plot with number '{plot_number}' already exists in this project."})


        plot = Plots.objects.create(**validated_data)
        for file_data in files_data:
            PlotsDocuments.objects.create(plot=plot, **file_data)
        return plot

    def update(self, instance, validated_data):
        files_data = validated_data.pop("files", [])
        project = validated_data.get('project', instance.project)
        project_id=project.id
        plot_number = validated_data.get('plot_number', instance.plot_number)
        
        if Plots.objects.filter(project=project, plot_number=plot_number).exclude(id=instance.id).exists() and project_id!=5:
            raise ValidationError({"error": f"A plot with number '{plot_number}' already exists in this project."})
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        for file_data in files_data:
            file_id = file_data.get("id", None)
            if file_id:
                file = PlotsDocuments.objects.get(id=file_id, plot=instance)
                file.description = file_data.get("description", file.description)
                file.type = file_data.get("type", file.type)
                if "file" in file_data:
                    file.file = file_data.get("file", file.file)
                file.save()
            else:
                PlotsDocuments.objects.create(plot=instance, **file_data)

        return instance


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
