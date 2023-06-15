from rest_framework import viewsets
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
            queryset = queryset.filter(status=plot_status)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class ResalePlotListView(ListAPIView):
    serializer_class = ResalePlotsSerializer
    queryset = Plots.objects.annotate(booking_count=Count('booking_details')).filter(
        booking_count__gt=1).prefetch_related(
            Prefetch('booking_details',
                     queryset=Booking.objects.select_related('customer'))
    )
