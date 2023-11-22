from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from .serializers import PlotsSerializer, ResalePlotsSerializer
from .models import Plots
from booking.models import Booking
from django.db.models import Count, Prefetch


class PlotsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Plots to be viewed or edited.
    """
    serializer_class = PlotsSerializer

    def get_queryset(self):
        queryset = Plots.objects.all()
        project_id = self.request.query_params.get('project')
        plot_status = self.request.query_params.get('status')

        # active,sold,
        if plot_status:
            if plot_status=="resale":
                    queryset = queryset.annotate(resale_count=Count('resale_plots')).filter(
                    resale_count__gte=1)
            else:
                queryset = queryset.filter(status=plot_status)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        sorted_queryset = sorted(
            queryset,
            key=lambda x: (len(x.plot_number), int(''.join(filter(str.isdigit, x.plot_number))))
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
