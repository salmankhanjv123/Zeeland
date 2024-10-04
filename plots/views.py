from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from .serializers import PlotsSerializer, ResalePlotsSerializer
from .models import Plots,PlotsDocuments
from booking.models import Booking
from django.db.models import Count, Prefetch


class PlotsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Plots to be viewed or edited.
    """
    serializer_class = PlotsSerializer

    def get_queryset(self):
        subplots_prefetch = Prefetch('sub_plots', queryset=Plots.objects.all().select_related('parent_plot'))
        files_prefetch = Prefetch('files', queryset=PlotsDocuments.objects.all())
        queryset = Plots.objects.all().prefetch_related(files_prefetch,subplots_prefetch).select_related('parent_plot')
        
        project_id = self.request.query_params.get('project')
        customer_id = self.request.query_params.get('customer_id')
        plot_status = self.request.query_params.get('status')
        plot_type=self.request.query_params.get('plot_type')

        # active,sold,
        if plot_status:
            queryset = queryset.filter(status=plot_status)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        if customer_id:
            queryset = queryset.filter(booking__customer_id=customer_id)
        if plot_type:
            queryset = queryset.filter(type=plot_type)
        return queryset
   
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        sorted_queryset = sorted(
            queryset,
            key=lambda x: (
            len(x.plot_number),
            int(''.join(filter(str.isdigit, x.plot_number))) if any(char.isdigit() for char in x.plot_number) else 0
        )
        )
        serializer = self.get_serializer(sorted_queryset, many=True)
        return Response(serializer.data)


class ResalePlotListView(ListAPIView):
    serializer_class = ResalePlotsSerializer

    def get_queryset(self):
        queryset = Plots.objects.annotate(booking_count=Count('booking_details')).filter(
            booking_count__gt=1).prefetch_related(
                Prefetch('booking_details',
                         queryset=Booking.objects.select_related('customer'))
        )

        project_id = self.request.query_params.get('project_id')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
