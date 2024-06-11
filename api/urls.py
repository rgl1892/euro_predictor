from django.urls import path
from . import views

urlpatterns = [
    path('predictions',views.Predictor.as_view())
]