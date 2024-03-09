from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import ProjectsSerializer,ProjectsBalanceSheetSerializer
from .models import Projects,ProjectsBalanceSheet




class ProjectsViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Projects to be viewed or edited.
    """
    queryset = Projects.objects.all()
    serializer_class = ProjectsSerializer



class ProjectsBalanceSheetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows Projects to be viewed or edited.
    """
    serializer_class = ProjectsBalanceSheetSerializer


    def get_queryset(self):
        queryset = ProjectsBalanceSheet.objects.all()
        date = self.request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        return queryset




class ProjectsBalanceBulkUpdateCreateAPIView(APIView):
    def post(self, request, format=None):
        data = request.data
        serializer = ProjectsBalanceSheetSerializer(data=data, many=True)
        serializer.is_valid(raise_exception=True)
        processed_data = []
        for item in serializer.validated_data:
            item_id=item["id"]
            item["user"]=item["user"].id
            # Check if the item has an ID, if yes, update the existing object
            if item_id is not None:
                instance = ProjectsBalanceSheet.objects.get(pk=item['id'])
                serializer_instance = ProjectsBalanceSheetSerializer(instance, data=item)
                serializer_instance.is_valid(raise_exception=True)
                serializer_instance.save()
                processed_data.append(serializer_instance.data)
            else:
                # Create a new object
                serializer_new = ProjectsBalanceSheetSerializer(data=item)
                serializer_new.is_valid(raise_exception=True)
                serializer_new.save()
                processed_data.append(serializer_new.data)

            return Response(processed_data, status=status.HTTP_200_OK)
