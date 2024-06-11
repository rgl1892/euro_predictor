from rest_framework import serializers
from predictor.models import *
from django.contrib.auth.models import User
        
class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['match_number']

class ScoreSerializer(serializers.ModelSerializer):
    match_number = MatchSerializer(many=False,read_only=True)
    class Meta:
        model = Score
        fields = ['id','country','home_away','match_number']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username']

class PredictionSerializer(serializers.ModelSerializer):
    match_choice = ScoreSerializer(many=False,read_only=True)
    user = UserSerializer(many=False,read_only=True)
    class Meta:
        model = Prediction
        fields = ['id','country','user','score','score_aet','points','penalties','exact','match_choice']
        depth = 2