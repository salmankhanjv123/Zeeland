from rest_framework import viewsets, status
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BookingSerializer, BookingForPaymentsSerializer, TokenSerializer,PlotResaleSerializer
from .models import Booking, Token,PlotResale
from payments.models import BankTransaction
from django.db.models import Q
from rest_framework.views import APIView
class BookingViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Booking to be viewed or edited.
    """
    serializer_class = BookingSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        plot_id = self.request.query_params.get('plot_id')
        plot_type = self.request.query_params.get('plot_type')
        customer_id = self.request.query_params.get('customer_id')
        status=self.request.query_params.get('status') 
        booking_type=self.request.query_params.get('booking_type')   
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        
        query_filters=Q()
        if booking_type:
            query_filters &= Q(booking_type=booking_type)
        if status:
            query_filters &= Q(status=status)
        if project_id:
            query_filters &= Q(project_id=project_id)
        if plot_id:
            query_filters &= Q(plots=plot_id)
        if plot_type:
            query_filters &= Q(plot__type=plot_type)
        if customer_id:
            query_filters &= Q(customer_id=customer_id)
        if start_date and end_date:
            query_filters &= Q(booking_date__gte=start_date) & Q(booking_date__lte=end_date)
        queryset = Booking.objects.filter(query_filters).select_related('customer','dealer','bank').prefetch_related("files","plots")
        return queryset
    
    def perform_destroy(self, instance):
        plots = instance.plots.all()
        for plot in plots:
            plot.status = "active"
            plot.save()
        super().perform_destroy(instance)

class BookingForPaymentsListView(ListAPIView):
    """
    API endpoint that lists Bookings for payments.
    """
    serializer_class = BookingForPaymentsSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        customer_id = self.request.query_params.get('customer_id')
        dealer_id = self.request.query_params.get('dealer_id')
        query_filters=Q()
        if project_id:
            query_filters &= Q(project_id=project_id)
        if customer_id:
            query_filters &= Q(customer_id=customer_id)
        if dealer_id:
            query_filters &= Q(dealer_id=dealer_id)
        queryset = Booking.objects.filter(query_filters).select_related('customer', 'plot','dealer')
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


class TokenViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Token to be viewed or edited.
    """
    serializer_class = TokenSerializer

    def get_queryset(self):
        project_id = self.request.query_params.get('project')
        plot_id = self.request.query_params.get('plot_id')
        plot_type = self.request.query_params.get('plot_type')
        customer_id = self.request.query_params.get('customer_id')
        status=self.request.query_params.get('status') 
        start_date = self.request.query_params.get("start_date")
        end_date = self.request.query_params.get("end_date")
        
        query_filters=Q()

        if status:
            query_filters &= Q(status=status)
        if project_id:
            query_filters &= Q(project_id=project_id)
        if plot_id:
            query_filters &= Q(plot_id=plot_id)
        if plot_type:
            query_filters &= Q(plot__type=plot_type)
        if customer_id:
            query_filters &= Q(customer_id=customer_id)
        if start_date and end_date:
            query_filters &= Q(date__gte=start_date) & Q(date__lte=end_date)
        queryset = Token.objects.filter(query_filters).select_related('customer','bank').prefetch_related("files",'plot')
        return queryset

    def perform_destroy(self, instance):
        # Delete all related bank transactions
        BankTransaction.objects.filter(
            related_table='token',
            related_id=instance.id
        ).delete()

        # Then delete the journal entry
        instance.delete()

class PlotResaleViewSet(viewsets.ModelViewSet):
    serializer_class = PlotResaleSerializer

    def get_queryset(self):
        queryset = PlotResale.objects.all().select_related("booking__customer")
        project_id = self.request.query_params.get('project')
        plot_id = self.request.query_params.get('plot_id')
        if project_id:
            queryset = queryset.filter(booking__project=project_id)
        if plot_id:
            queryset=queryset.filter(plot_id=plot_id)
        return queryset
    
    def create(self, request, *args, **kwargs):
        booking_id = request.data.get("booking")
        if booking_id:
            try:
                booking = Booking.objects.get(pk=booking_id)
                booking.status = "close"
                booking.plot.status="active"
                booking.plot.save()
                booking.save()
            except Booking.DoesNotExist:
                return Response({"booking": ["Booking not found."]}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)

    def perform_destroy(self, instance):
        booking = instance.booking
        booking.status = "active"
        booking.plot.status = "sold"
        booking.plot.save()
        booking.save()
        super().perform_destroy(instance)




# Define the allowed statuses

class UpdateTokenStatusView(APIView):
    def patch(self, request, token_id):
        try:
            token = Token.objects.get(pk=token_id)
        except Token.DoesNotExist:
            return Response({"error": "Token not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get the status value from the request data
        status_value = request.data.get('status')
        if not status_value:
            return Response({"error": "Status field is required"}, status=status.HTTP_400_BAD_REQUEST)
        allowed_statuses = ['pending', 'accepted', 'cancelled']
        # Validate the status value
        if status_value not in allowed_statuses:
            return Response({"error": f"Invalid status. Allowed statuses are {', '.join(allowed_statuses)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Update the token status
        token.status = status_value
        token.save()

        return Response({"status": token.status}, status=status.HTTP_200_OK)
