from django.shortcuts import render
from rest_framework import viewsets, permissions, status, generics
from django.contrib.auth import get_user_model
from .serializers import UsersSerializer, CreateUsersSerializer, BlacklistTokenSerializer
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

#* Index view for the API
def index(request):
    return HttpResponse("Welcome to the REST API!")

#* Create Users ViewSet
class CreateUsersViewSet(generics.CreateAPIView):
    serializer_class = CreateUsersSerializer
    permission_classes = [permissions.AllowAny]
    queryset = User.objects.all()


#* Users ViewSet
class UsersViewSet(viewsets.ModelViewSet):

    serializer_class = UsersSerializer
    permission_classes = [
        permissions.IsAuthenticated
    ]
    queryset = User.objects.all()

    def get_queryset(self):

        return self.queryset.filter(username=self.request.user)

    def perform_create(self, serializer):
        serializer.save(username=self.request.user)

#* Blacklist Token View
class BlacklistTokenView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request,):
        serializer = BlacklistTokenSerializer(data=request.data)
        if serializer.is_valid():
            try:
                refresh_token = request.data["refresh_token"]
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response(status=status.HTTP_202_ACCEPTED)
            except Exception:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)