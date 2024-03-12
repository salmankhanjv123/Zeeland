from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProjectsSerializer,BalanceSheetSerializer
from .models import Projects,BalanceSheet,BalanceSheetDetails,BalanceSheetAmountDetails




class ProjectsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Projects to be viewed or edited.
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer



class BalanceSheetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Projects to be viewed or edited.
    """
    serializer_class = BalanceSheetSerializer


    def get_queryset(self):
        queryset = BalanceSheet.objects.all()
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        return queryset




# class ProjectsBalanceBulkUpdateCreateAPIView(APIView):
#     def post(self, request, format=None):
#         data = request.data
#         processed_data = []
#         for item in data:
#             item_id = item.get("id")  
#             if item_id is not None:
#                 instance = ProjectsBalanceSheet.objects.get(pk=item_id)
#                 serializer_instance = ProjectsBalanceSheetSerializer(instance, data=item)
#                 serializer_instance.is_valid(raise_exception=True)
#                 serializer_instance.save()
#                 processed_data.append(serializer_instance.data)
#             else:
#                 serializer_new = ProjectsBalanceSheetSerializer(data=item)
#                 serializer_new.is_valid(raise_exception=True)
#                 serializer_new.save()
#                 processed_data.append(serializer_new.data)

#         return Response(processed_data, status=status.HTTP_200_OK)

