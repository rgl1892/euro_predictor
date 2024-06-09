from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError

from .forms import EditAuthForm,EditUserForm
from .models import Country,Group,Score,Prediction,Match

def create_user_predictions(request):
    matches = Score.objects.all()
    for item in matches:
        Prediction.objects.create(match_choice=item,score=None,score_aet=None,penalties=None,result=None,user=request.user)

def create_51_matches():
    [Match.objects.create(match_number=x+3,id=x+3) for x in range(51)]


class Home(View):

    template_name = 'predictor/home.html'

    def get(self, request):
        # create_user_predictions(request)
        
        

        return render(request, self.template_name)

class WorldRankings(View):
    template_name = 'predictor/world_rankings.html'
    def get(self, request):
        # create_user_predictions(request)
        countries = Country.objects.order_by('fifa_ranking')
        context = {
            'countries':countries
        }
        

        return render(request, self.template_name, context)

def signUpUser(request):
    if request.method == 'GET':

        return render(request, 'predictor/login/signUpUser.html', {'form': EditUserForm()})

    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(
                    request.POST['username'], password=request.POST['password1'])
                user.save()
                login(request, user)
                create_user_predictions(request)
                return redirect('homepage')
            except IntegrityError:
                return render(request, 'predictor/login/signUpUser.html', {'form': EditUserForm(), 'error': 'Username Already Taken'})

        else:

            return render(request, 'predictor/login/signUpUser.html', {'form': EditUserForm(), 'error': 'Passwords did not match'})


def logOutUser(request):
    logout(request)
    return redirect('homepage')


def logInUser(request):
    if request.method == 'GET':
        return render(request, 'predictor/login/login.html', {'form': EditAuthForm()})

    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST['password'])
        if user == None:
            return render(request, 'predictor/login/login.html', {'form': EditAuthForm(), 'error': 'Unknown User / Incorrect Password'})
        else:
            login(request, user)
            return redirect('homepage')
        
def get_group_tables(request):
    groups = Group.objects.all()
    matches = Match.objects.all()
    scores = Prediction.objects.filter(user=request.user).order_by('match_choice__match_number')
    grouped = [[[score for score in scores.filter(match_choice__match_number=event)] for event in matches.filter(score__group=group)][::2] for group in groups]
    country = {}
    for group in grouped:
        for event in group:
            country[f'{event[0].match_choice.country.name}'] =  {'country':event[0].match_choice.country.name,'wins':0,'losses':0, 'draws':0, 'goals_for':0,'goals_against':0,'group':event[0].match_choice.group.letter,'fifa':event[0].match_choice.country.fifa_points}
    for group in grouped:
        for event in group:
            try:
                if event[0].score > event[1].score:
                    country[f'{event[0].match_choice.country.name}']['wins'] += 1
                    country[f'{event[1].match_choice.country.name}']['losses'] += 1
                elif event[0].score < event[1].score:
                    country[f'{event[1].match_choice.country.name}']['wins'] += 1
                    country[f'{event[0].match_choice.country.name}']['losses'] += 1
                else:
                    country[f'{event[0].match_choice.country.name}']['draws'] += 1
                    country[f'{event[1].match_choice.country.name}']['draws'] += 1
                country[f'{event[0].match_choice.country.name}']['goals_for'] += event[0].score
                country[f'{event[1].match_choice.country.name}']['goals_for'] += event[1].score
                country[f'{event[0].match_choice.country.name}']['goals_against'] += event[1].score
                country[f'{event[1].match_choice.country.name}']['goals_against'] += event[0].score
            except:
                continue
    for item in country:
        country[item]['points'] = country[item]['wins'] * 3 + country[item]['draws']
        country[item]['ranking'] = country[item]['points'] + (country[item]['goals_for'] - country[item]['goals_against'])*0.01 + (country[item]['goals_for'])*0.0001 + float(country[item]['fifa'])* 0.000000001
    group_letters = ['A','B','C','D','E','F']
    grouped_tour = []
    for group in group_letters:
        group_team = []
        for row in country:
            if country[row]['group'] == group:
                group_team.append(country[row])
        grouped_tour.append(group_team)

    stuff = [sorted(row,key = lambda x: x['ranking'],reverse=True) for row in grouped_tour]
    third_teams = [row[2] for row in stuff]
    best_thirds = sorted(third_teams ,key= lambda x: x['ranking'],reverse=True)
    context = {
            'grouped':grouped,
            'stuff':stuff,
            'best_thirds': best_thirds
        }
    return context


class PredictionView(View):

    template_name = 'predictor/prediction/prediction.html'

    def get(self, request):
        context = get_group_tables(request)
        return render(request,self.template_name,context)
    
    def post(self, request):
        for x in request.POST:
            if x != 'csrfmiddlewaretoken':
                if request.POST[f'{x}'] != '':
                    Prediction.objects.filter(match_choice=x,user=request.user).update(score=request.POST[f'{x}'])
                else:
                    Prediction.objects.filter(match_choice=x,user=request.user).update(score=None)
        context = get_group_tables(request)
        return render(request,self.template_name,context)
    
