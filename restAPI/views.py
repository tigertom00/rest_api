from django.shortcuts import render
from rest_framework import viewsets, permissions
from django.contrib.auth import get_user_model
from .serializers import UsersSerializer
from django.http import HttpResponse

def index(request):
    return HttpResponse("Welcome to the REST API!")


# User views
User = get_user_model()


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