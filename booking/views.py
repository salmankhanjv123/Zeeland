from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BookingSerializer, BookingForPaymentsSerializer
from .models import Booking


class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Booking to be viewed or edited.
    """
    serializer_class = BookingSerializer

    def get_queryset(self):
        queryset = Booking.objects.all().select_related('customer', 'plot')
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


class BookingForPaymentsListView(ListAPIView):
    """
    API endpoint that lists Bookings for payments.
    """
    serializer_class = BookingForPaymentsSerializer

    def get_queryset(self):
        queryset = Booking.objects.all().select_related('customer', 'plot').values(
            'id', 'booking_id', 'customer__name', 'plot__plot_number', 'project_id')
        project_id = self.request.query_params.get('project')
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset


@api_view(['GET'])
def latest_booking_id(request, project):
    try:
        latest_booking = Booking.objects.filter(
            project_id=project).latest('created_at')
        booking_id = int(latest_booking.booking_id.split('-')[1]) + 1
    except Booking.DoesNotExist:
        booking_id = 1
    booking_id_str = str(project) + \
        '-' + str(booking_id).zfill(3)
    return Response({'booking_id': booking_id_str}, status=status.HTTP_200_OK)
