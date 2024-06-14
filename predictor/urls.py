from django.contrib import admin
from django.urls import path, include
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('',views.Home.as_view(),name='homepage' ),
    path('login',views.logInUser,name='login'),
    path('logout',views.logOutUser,name='logout'),
    path('world_rankings',views.WorldRankings.as_view(),name='world_rankings'),
    path('sign_up_user', views.signUpUser,name='sign_up_user'),
    path('group_entry',views.PredictionView.as_view(),name='group_entry'),
    path('actual_entry',views.ActualView.as_view(),name='actual_entry'),
    path('winners',views.WinnersView.as_view(),name='winners'),
    path('stats',views.StatsView.as_view(),name='stats'),
    path('account',views.AccountView.as_view(),name='account'),
    path('closed_predictions',views.ClosedPredictionView.as_view(),name='closed_predictions'),
    path('predictions/<int:id>',views.SeeUserPredictions.as_view(),name='predictions'),
]