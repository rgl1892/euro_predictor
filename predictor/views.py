from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError

from .forms import EditAuthForm,EditUserForm,AccountForm
from .models import Country,Group,Score,Prediction,Match,Winner

def create_user_predictions(request):
    matches = Score.objects.all()
    for item in matches:
        Prediction.objects.create(match_choice=item,score=None,score_aet=None,penalties=None,user=request.user,country=str(item.country.name))

def create_51_matches():
    [Match.objects.create(match_number=x+3,id=x+3) for x in range(51)]

def check_user_points(request):

    filled_in_scores = Prediction.objects.filter(actual='Actual').exclude(score__isnull=True)
    per_match = [[item for item in Prediction.objects.filter(actual='Actual',match_choice__match_number=x).exclude(score__isnull=True)] for x in range(1,51)]
    users = User.objects.exclude(username='Actual_Scores')
    per_match_users =[[[item for item in Prediction.objects.filter(user=user,match_choice__match_number=x).exclude(score__isnull=True)] for x in range(1,51)] for user in users]
    for user_row in per_match_users:
        for index,matches in enumerate(user_row):
            if per_match[index] != []:
                points = 0
                exact = 0
                if matches[0].score > matches[1].score and per_match[index][0].score > per_match[index][1].score or matches[0].score < matches[1].score and per_match[index][0].score < per_match[index][1].score:
                    points += 1

                if matches[0].score - matches[1].score == per_match[index][0].score - per_match[index][1].score:
                    points += 1

                if matches[0].score == per_match[index][0].score and matches[1].score == per_match[index][1].score:
                    points += 2
                    exact += 1
                if matches[0].match_choice.stage == 'Finals':
                    if matches[0].country == per_match[index][0].country:
                        points +=1
                    if matches[1].country == per_match[index][1].country:
                        points +=1
                    if matches[0].country == per_match[index][1].country:
                        points +=1
                    if matches[1].country == per_match[index][0].country:
                        points +=1
                matches[0].points = points
                matches[1].points = points
                matches[0].exact = exact
                matches[1 ].exact = exact
                matches[0].save()
                matches[1].save()

    
class Home(View):

    template_name = 'predictor/home.html'

    def get(self, request):    
        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')
        points = [int(sum([item.points for item in Prediction.objects.filter(user=user) if item.points != None])/2) for user in users]
        exact = [int(sum([item.exact for item in Prediction.objects.filter(user=user) if item.points != None])/2) for user in users]
        
        leaderboard = []
        for i in range(len(users)):
            leaderboard.append([users[i],points[i],exact[i]])
        
        context = {
            'leaderboard':leaderboard
        }
        return render(request, self.template_name,context)

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
        
def get_group_tables(request,user_name):
    groups = Group.objects.all()
    matches = Match.objects.all()
    scores = Prediction.objects.filter(user=user_name).order_by('match_choice__match_number')
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
    third_groups = []
    
    best_thirds = sorted(third_teams ,key= lambda x: x['ranking'],reverse=True)
    for x in best_thirds[:4]:
        third_groups.append(x['group'])
    
    context = {
            'grouped':grouped,
            'stuff':stuff,
            'best_thirds': best_thirds,
            'third_groups':third_groups,
        }
    
    final_matches = Score.objects.filter(stage='Finals')
    now_preds = [[item for item in Prediction.objects.filter(user=user_name,match_choice__match_number=match_item.match_number)] for match_item in final_matches][::2]
        
    context['now_preds'] = now_preds[:8]
    context['quarters'] = now_preds[8:12]
    context['semis'] = now_preds[12:14]
    context['final'] = [now_preds[14]]
    return context


class PredictionView(View):

    template_name = 'predictor/prediction/prediction.html'

    def get(self, request):
        context = get_group_tables(request,request.user)
        return render(request,self.template_name,context)
    
    def post(self, request):
        try:
            out = request.POST['groups']
        except:
            out = False
        if out == 'groups':
            print('hi')
            for x in request.POST:
                if x != 'csrfmiddlewaretoken' and x!= 'groups':
                    if request.POST[f'{x}'] != '':
                        Prediction.objects.filter(match_choice=x,user=request.user).update(score=request.POST[f'{x}'])
                    else:
                        Prediction.objects.filter(match_choice=x,user=request.user).update(score=None)
            context = get_group_tables(request,request.user)
            pred = Prediction.objects.filter(user=request.user).exclude(score__isnull=True).exclude(match_choice__group__letter__isnull=True)
            third_groups = sorted(context['third_groups'])
            options = {
            "['A', 'B', 'C', 'D']":[1,4,2,3],
            "['A', 'B', 'C', 'E']":[1,5,2,3],
            "['A', 'B', 'C', 'F']":[1,6,2,3],
            "['A', 'B', 'D', 'E']":[4,5,1,2],
            "['A', 'B', 'D', 'F']":[4,6,1,2],
            "['A', 'B', 'E', 'F']":[5,6,2,1],
            "['A', 'C', 'D', 'E']":[5,4,3,1],
            "['A', 'C', 'D', 'F']":[6,4,3,1],
            "['A', 'C', 'E', 'F']":[5,6,3,1],
            "['A', 'D', 'E', 'F']":[5,6,4,1],
            "['B', 'C', 'D', 'E']":[5,4,2,3],
            "['B', 'C', 'D', 'F']":[6,4,3,2],
            "['B', 'C', 'E', 'F']":[6,5,3,2],
            "['B', 'D', 'E', 'F']":[6,5,4,2],
            "['C', 'D', 'E', 'F']":[6,5,4,3],
            }
            
            third_teams = options[f'{third_groups}']
            

            
            if len(pred) == 72:
                Prediction.objects.filter(user=request.user,match_choice__match_number=37,match_choice__home_away='Home').update(country=context['stuff'][0][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=37,match_choice__home_away='Away').update(country=context['stuff'][2][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=38,match_choice__home_away='Home').update(country=context['stuff'][0][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=38,match_choice__home_away='Away').update(country=context['stuff'][1][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=39,match_choice__home_away='Home').update(country=context['stuff'][1][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=39,match_choice__home_away='Away').update(country=context['stuff'][third_teams[0]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=40,match_choice__home_away='Home').update(country=context['stuff'][2][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=40,match_choice__home_away='Away').update(country=context['stuff'][third_teams[1]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=41,match_choice__home_away='Home').update(country=context['stuff'][5][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=41,match_choice__home_away='Away').update(country=context['stuff'][third_teams[2]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Home').update(country=context['stuff'][3][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Away').update(country=context['stuff'][4][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Home').update(country=context['stuff'][4][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Away').update(country=context['stuff'][third_teams[3]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=44,match_choice__home_away='Home').update(country=context['stuff'][3][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=44,match_choice__home_away='Away').update(country=context['stuff'][5][1]['country'])

        if list(request.POST.keys())[-1] == 'last-16':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'last-16':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            last_16_range = range(37,45)
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=x) for x in last_16_range]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)

            Prediction.objects.filter(user=request.user,match_choice__match_number=45,match_choice__home_away='Home').update(country=winners[2])
            Prediction.objects.filter(user=request.user,match_choice__match_number=45,match_choice__home_away='Away').update(country=winners[0])
            Prediction.objects.filter(user=request.user,match_choice__match_number=46,match_choice__home_away='Home').update(country=winners[4])
            Prediction.objects.filter(user=request.user,match_choice__match_number=46,match_choice__home_away='Away').update(country=winners[5])
            Prediction.objects.filter(user=request.user,match_choice__match_number=47,match_choice__home_away='Home').update(country=winners[6])
            Prediction.objects.filter(user=request.user,match_choice__match_number=47,match_choice__home_away='Away').update(country=winners[7])
            Prediction.objects.filter(user=request.user,match_choice__match_number=48,match_choice__home_away='Home').update(country=winners[3])
            Prediction.objects.filter(user=request.user,match_choice__match_number=48,match_choice__home_away='Away').update(country=winners[1])

        if list(request.POST.keys())[-1] == 'quarters':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'quarters':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            range_to_use = range(45,49)
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=x) for x in range_to_use]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
            Prediction.objects.filter(user=request.user,match_choice__match_number=49,match_choice__home_away='Home').update(country=winners[0])
            Prediction.objects.filter(user=request.user,match_choice__match_number=49,match_choice__home_away='Away').update(country=winners[1])
            Prediction.objects.filter(user=request.user,match_choice__match_number=50,match_choice__home_away='Home').update(country=winners[2])
            Prediction.objects.filter(user=request.user,match_choice__match_number=50,match_choice__home_away='Away').update(country=winners[3])
        
        if list(request.POST.keys())[-1] == 'semis':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'semis':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            range_to_use = range(49,51)
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=x) for x in range_to_use]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
            Prediction.objects.filter(user=request.user,match_choice__match_number=51,match_choice__home_away='Home').update(country=winners[0])
            Prediction.objects.filter(user=request.user,match_choice__match_number=51,match_choice__home_away='Away').update(country=winners[1])


        if list(request.POST.keys())[-1] == 'final':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'final':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=51)]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                Winner.objects.update_or_create(user=request.user,winner=winners[0])

        context = get_group_tables(request,request.user)
        
        return render(request,self.template_name,context)
    
class WinnersView(View):
    template_name = 'predictor/summary/winners.html'

    def get(self,request):

        winners_list = Winner.objects.all()

        context = {
            'winners_list':winners_list
        }

        return render(request,self.template_name,context)

class ActualView(View):

    template_name = 'predictor/actual/actual.html'

    def get(self, request):
        check_user_points(request)
        context = get_group_tables(request,request.user)
        return render(request,self.template_name,context)
    
    def post(self, request):
        
        try:
            out = request.POST['groups']
        except:
            out = False
        if out == 'groups':
            for x in request.POST:
                if x != 'csrfmiddlewaretoken' and x!= 'groups':
                    if request.POST[f'{x}'] != '':
                        Prediction.objects.filter(match_choice=x,user=request.user).update(score=request.POST[f'{x}'])
                    else:
                        Prediction.objects.filter(match_choice=x,user=request.user).update(score=None)
            context = get_group_tables(request,request.user)
            pred = Prediction.objects.filter(user=request.user).exclude(score__isnull=True).exclude(match_choice__group__letter__isnull=True)
            third_groups = sorted(context['third_groups'])
            options = {
            "['A', 'B', 'C', 'D']":[1,4,2,3],
            "['A', 'B', 'C', 'E']":[1,5,2,3],
            "['A', 'B', 'C', 'F']":[1,6,2,3],
            "['A', 'B', 'D', 'E']":[4,5,1,2],
            "['A', 'B', 'D', 'F']":[4,6,1,2],
            "['A', 'B', 'E', 'F']":[5,6,2,1],
            "['A', 'C', 'D', 'E']":[5,4,3,1],
            "['A', 'C', 'D', 'F']":[6,4,3,1],
            "['A', 'C', 'E', 'F']":[5,6,3,1],
            "['A', 'D', 'E', 'F']":[5,6,4,1],
            "['B', 'C', 'D', 'E']":[5,4,2,3],
            "['B', 'C', 'D', 'F']":[6,4,3,2],
            "['B', 'C', 'E', 'F']":[6,5,3,2],
            "['B', 'D', 'E', 'F']":[6,5,4,2],
            "['C', 'D', 'E', 'F']":[6,5,4,3],
            }
            
            third_teams = options[f'{third_groups}']
            

            
            if len(pred) == 72:
                Prediction.objects.filter(user=request.user,match_choice__match_number=37,match_choice__home_away='Home').update(country=context['stuff'][0][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=37,match_choice__home_away='Away').update(country=context['stuff'][2][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=38,match_choice__home_away='Home').update(country=context['stuff'][0][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=38,match_choice__home_away='Away').update(country=context['stuff'][1][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=39,match_choice__home_away='Home').update(country=context['stuff'][1][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=39,match_choice__home_away='Away').update(country=context['stuff'][third_teams[0]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=40,match_choice__home_away='Home').update(country=context['stuff'][2][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=40,match_choice__home_away='Away').update(country=context['stuff'][third_teams[1]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=41,match_choice__home_away='Home').update(country=context['stuff'][5][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=41,match_choice__home_away='Away').update(country=context['stuff'][third_teams[2]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Home').update(country=context['stuff'][3][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Away').update(country=context['stuff'][4][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Home').update(country=context['stuff'][4][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Away').update(country=context['stuff'][third_teams[3]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=44,match_choice__home_away='Home').update(country=context['stuff'][3][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=44,match_choice__home_away='Away').update(country=context['stuff'][5][1]['country'])

        if list(request.POST.keys())[-1] == 'last-16':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'last-16':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            last_16_range = range(37,45)
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=x) for x in last_16_range]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)

            Prediction.objects.filter(user=request.user,match_choice__match_number=45,match_choice__home_away='Home').update(country=winners[2])
            Prediction.objects.filter(user=request.user,match_choice__match_number=45,match_choice__home_away='Away').update(country=winners[0])
            Prediction.objects.filter(user=request.user,match_choice__match_number=46,match_choice__home_away='Home').update(country=winners[4])
            Prediction.objects.filter(user=request.user,match_choice__match_number=46,match_choice__home_away='Away').update(country=winners[5])
            Prediction.objects.filter(user=request.user,match_choice__match_number=47,match_choice__home_away='Home').update(country=winners[6])
            Prediction.objects.filter(user=request.user,match_choice__match_number=47,match_choice__home_away='Away').update(country=winners[7])
            Prediction.objects.filter(user=request.user,match_choice__match_number=48,match_choice__home_away='Home').update(country=winners[3])
            Prediction.objects.filter(user=request.user,match_choice__match_number=48,match_choice__home_away='Away').update(country=winners[1])

        if list(request.POST.keys())[-1] == 'quarters':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'quarters':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            range_to_use = range(45,49)
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=x) for x in range_to_use]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
            Prediction.objects.filter(user=request.user,match_choice__match_number=49,match_choice__home_away='Home').update(country=winners[0])
            Prediction.objects.filter(user=request.user,match_choice__match_number=49,match_choice__home_away='Away').update(country=winners[1])
            Prediction.objects.filter(user=request.user,match_choice__match_number=50,match_choice__home_away='Home').update(country=winners[2])
            Prediction.objects.filter(user=request.user,match_choice__match_number=50,match_choice__home_away='Away').update(country=winners[3])
        
        if list(request.POST.keys())[-1] == 'semis':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'semis':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            range_to_use = range(49,51)
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=x) for x in range_to_use]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
            Prediction.objects.filter(user=request.user,match_choice__match_number=51,match_choice__home_away='Home').update(country=winners[0])
            Prediction.objects.filter(user=request.user,match_choice__match_number=51,match_choice__home_away='Away').update(country=winners[1])


        if list(request.POST.keys())[-1] == 'final':
            ids = []
            for x in dict(request.POST):
                if x != 'csrfmiddlewaretoken' and x != 'final':
                    ids.append(x[:x.find("-")])
                    ids = list(set(ids))
            new_dict = {}
            for key in request.POST:
                if request.POST[key] == '':
                    new_dict[key] = None
                else:
                    new_dict[key] = request.POST[key]
            for x in ids:
                Prediction.objects.filter(id=x).update(score=new_dict[f'{x}-score'],score_aet=new_dict[f'{x}-aet'],penalties=new_dict[f'{x}-pens'])

            
            
            get_winners = [Prediction.objects.filter(user=request.user,match_choice__match_number=51)]
            winners = []
            for match_played in get_winners:
                if match_played[0].penalties:
                    if match_played[0].score + match_played[0].score_aet*0.01 + match_played[0].penalties*0.0001 > match_played[1].score + match_played[1].score_aet*0.01 + match_played[1].penalties*0.0001:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                elif match_played[0].score_aet:
                    if match_played[0].score + match_played[0].score_aet*0.01 > match_played[1].score + match_played[1].score_aet*0.01:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)   
                else:
                    if match_played[0].score > match_played[1].score:
                        winners.append(match_played[0].country) 
                    else:
                        winners.append(match_played[1].country)
                Winner.objects.update_or_create(user=request.user,winner=winners[0])

        context = get_group_tables(request,request.user)
        
        return render(request,self.template_name,context)
    
class StatsView(View):
    template_name = 'predictor/stats/stats.html'

    def get(self,request):
        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')
        matches = Match.objects.all()
        teams_per_match = [Prediction.objects.filter(user__username='Actual_Scores',match_choice__match_number=item.match_number) for item in matches]
        context = {
            'users':users,
            'teams_per_match':teams_per_match,
        }
    
        return render(request,self.template_name,context)
    
class AccountView(View):

    template_name = 'predictor/login/account.html'

    def get(self,request):

        user = User.objects.filter(username=request.user)
        context = {
            'logged_in_user':user,
        }
        return render(request,self.template_name,context)
    
    def post(self,request):

        User.objects.filter(username=request.user).update(first_name=request.POST['first_name'],last_name=request.POST['last_name'])
        user = User.objects.filter(username=request.user)

        context = {
            'logged_in_user':user,
        }
        return render(request,self.template_name,context)

class ClosedPredictionView(View):

    template_name = 'predictor/prediction/closed_predictions.html'

    def get(self, request):
        context = get_group_tables(request,request.user)
        return render(request,self.template_name,context)
    
class SeeUserPredictions(View):
    template_name = 'predictor/prediction/closed_predictions.html'

    def get(self, request,id):
        user_name = User.objects.filter(id=id).get()
        context = get_group_tables(request,user_name)
        context['user_name'] = user_name

        return render(request,self.template_name,context)