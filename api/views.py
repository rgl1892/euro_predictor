from django.shortcuts import render
from rest_framework import generics,permissions
from .serializers import *
from predictor.models import *
from django_filters.rest_framework import DjangoFilterBackend

class Predictor(generics.ListAPIView):
    serializer_class = PredictionSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['user','match_choice__match_number']

    def get_queryset(self):
        user = self.request.user
        return Prediction.objects.all()
    
