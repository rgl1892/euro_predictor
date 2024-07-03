from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.core.cache import cache

from collections import Counter
from datetime import datetime
from datetime import timedelta
import math
from statistics import mean

from .forms import EditAuthForm,EditUserForm,AccountForm
from .models import Country,Group,Score,Prediction,Match,Winner

PREDICTION_KEY = 'predictions.all'

def create_user_predictions(request):
    matches = Score.objects.all()
    for item in matches:
        Prediction.objects.create(match_choice=item,score=None,score_aet=None,penalties=None,user=request.user,country=str(item.country.name))

def create_51_matches():
    [Match.objects.create(match_number=x+3,id=x+3) for x in range(51)]

def check_user_points(request):

    filled_in_scores = Prediction.objects.filter(actual='Actual').exclude(score__isnull=True)
    per_match = [[item for item in Prediction.objects.filter(actual='Actual',match_choice__match_number=x).exclude(score__isnull=True)] for x in range(1,51)]
    users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')
    per_match_users =[[[item for item in Prediction.objects.filter(user=user,match_choice__match_number=x).exclude(score__isnull=True)] for x in range(1,51)] for user in users]
    for user_row in per_match_users:
        if user_row[0] != []:
            for index,matches in enumerate(user_row):
                if per_match[index] != [] and matches != []:
                    points = 0
                    exact = 0
                    
                    if matches[0].score > matches[1].score and per_match[index][0].score > per_match[index][1].score or matches[0].score < matches[1].score and per_match[index][0].score < per_match[index][1].score:
                        points += 1
                    if matches[0].score == matches[1].score and per_match[index][0].score == per_match[index][1].score:
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
                    matches[1].exact = exact
                    matches[0].save()
                    matches[1].save()

def calculate_leaderboard():
    users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')
    points = [int(sum([item.points for item in Prediction.objects.filter(user=user) if item.points != None])/2) for user in users]
    right_results = [int(len([item.points for item in Prediction.objects.filter(user=user) if item.points == 1])/2) for user in users]
    right_gd = [int(len([item.points for item in Prediction.objects.filter(user=user) if item.points == 2])/2) for user in users]
    exact = [int(sum([item.exact for item in Prediction.objects.filter(user=user) if item.points != None])/2) for user in users]
    
    leaderboard = []
    for i in range(len(users)):
        leaderboard.append([users[i],points[i],exact[i],right_results[i],right_gd[i],exact[i]+right_results[i]+right_gd[i]])
    
    leaderboard = sorted(leaderboard,key=lambda x: (x[1],x[2]),reverse=True)
    max_number = max([x[2] for x in leaderboard])
    min_number = min([x[2] for x in leaderboard])
    min_array = [x for x in leaderboard if x[2] == min_number][0]

    for row in leaderboard:
        if row[2] == max_number:
            row.append(1)
        elif row == min_array:
            row.append(2)
        else:
            row.append(0)  
    counter = 0
    for x in range(len(leaderboard)):
        if x ==0:
            leaderboard[x].append(1)
        else:
            if leaderboard[x][1] == leaderboard[x-1][1]:
                leaderboard[x].append(leaderboard[x-1][7])
                counter += 1
            else:
                leaderboard[x].append(leaderboard[x-1][7]+1+counter)
                counter = 0


    transposed = list(map(list, zip(*leaderboard)))

    transposed_col = list(map(list, zip(*leaderboard)))[7]
    count_col = []
    count_val = Counter(transposed_col)
    for x in transposed_col:
        count_col.append(count_val[x])
    transposed.append(count_col)
    leaderboard = list(map(list, zip(*transposed)))

    for x in range(len(leaderboard)):
        if leaderboard[x][8] > 1:
            leaderboard[x].append(f'{leaderboard[x][7]}=')
        else:
            leaderboard[x].append(f'{leaderboard[x][7]}')
    return leaderboard

def update_score_table():
    actuals_home = Prediction.objects.filter(user__username='Actual_Scores',match_choice__home_away='Home',match_choice__stage='Finals')
    actuals_away = Prediction.objects.filter(user__username='Actual_Scores',match_choice__home_away='Away',match_choice__stage='Finals')
    [Score.objects.filter(home_away='Home',match_number=item.match_choice.match_number).update(country=Country.objects.filter(name=item.country).get().id) for item in actuals_home if item.country != 'None']
    [Score.objects.filter(home_away='Away',match_number=item.match_choice.match_number).update(country=Country.objects.filter(name=item.country).get().id) for item in actuals_away if item.country != 'None']



    
class Home(View):

    template_name = 'predictor/home.html'

    def get(self, request):  

        # location = [
        #     "Olympiastadion",
        #     'BVB Stadion Dortmund',
        #     'Arena AufSchalke',
        #     "Stadion Köln",
        #     "Düsseldorf Arena",
        #     "Frankfurt Stadion",
        #     "Fußball Arena München",
        #     "Fußball Arena München",
        #     "Arena Stuttgart",
        #     "Volksparkstadion"]
        # scores = Score.objects.filter(match_number=37)
        # for score in scores:
        #     score.location = location[0]
        #     score.date = datetime(2024,6,29,19)
        #     score.save()
        # scores = Score.objects.filter(match_number=38)
        # for score in scores:
        #     score.location = location[1]
        #     score.date = datetime(2024,6,29,16)
        #     score.save()
        # scores = Score.objects.filter(match_number=39)
        # for score in scores:
        #     score.location = location[3]
        #     score.date = datetime(2024,6,30,19)
        #     score.save()
        # scores = Score.objects.filter(match_number=40)
        # for score in scores:
        #     score.location = location[2]
        #     score.date = datetime(2024,6,30,16)
        #     score.save()
        # scores = Score.objects.filter(match_number=41)
        # for score in scores:
        #     score.location = location[5]
        #     score.date = datetime(2024,7,1,19)
        #     score.save()
        # scores = Score.objects.filter(match_number=42)
        # for score in scores:
        #     score.location = location[4]
        #     score.date = datetime(2024,7,1,16)
        #     score.save()
        # scores = Score.objects.filter(match_number=43)
        # for score in scores:
        #     score.location = location[6]
        #     score.date = datetime(2024,7,2,19)
        #     score.save()
        # scores = Score.objects.filter(match_number=44)
        # for score in scores:
        #     score.location = location[7]
        #     score.date = datetime(2024,7,2,16)
        #     score.save()

        update_score_table()
        leaderboard = calculate_leaderboard()

        today_date = datetime.strftime(datetime.today(),"%Y-%m-%d")
        today_matches = Score.objects.filter(date__date=today_date).order_by('date')
        today_matches = [today_matches[i:i+2] for i in range(0,len(today_matches),2)]




        if request.user.is_authenticated and str(request.user) != 'richardlongdon':
            today = []
            today_scores = [[Prediction.objects.filter(match_choice=game,user__username=request.user).get() for game in match] for match in today_matches]
            for x ,y in zip(today_matches,today_scores):
                today.append([x,y])
        else:
            today= today_matches

        context = {
            'leaderboard':leaderboard,
            'today_matches':today,
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

    template_name = 'predictor/prediction/closed_predictions.html'

    def get(self, request):
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
            print(third_groups)
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
                Prediction.objects.filter(user=request.user,match_choice__match_number=41,match_choice__home_away='Away').update(country=context['stuff'][third_teams[3]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Home').update(country=context['stuff'][3][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Away').update(country=context['stuff'][4][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Home').update(country=context['stuff'][4][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Away').update(country=context['stuff'][third_teams[2]-1][2]['country'])
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
            print(third_teams)
            

            
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
                Prediction.objects.filter(user=request.user,match_choice__match_number=41,match_choice__home_away='Away').update(country=context['stuff'][third_teams[3]-1][2]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Home').update(country=context['stuff'][3][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=42,match_choice__home_away='Away').update(country=context['stuff'][4][1]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Home').update(country=context['stuff'][4][0]['country'])
                Prediction.objects.filter(user=request.user,match_choice__match_number=43,match_choice__home_away='Away').update(country=context['stuff'][third_teams[2]-1][2]['country'])
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

            get_winners = [x for x in get_winners if str(x[0].score) != 'None']
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
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=45,match_choice__home_away='Home').update(country=winners[2])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=45,match_choice__home_away='Away').update(country=winners[0])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=46,match_choice__home_away='Home').update(country=winners[4])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=46,match_choice__home_away='Away').update(country=winners[5])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=47,match_choice__home_away='Home').update(country=winners[6])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=47,match_choice__home_away='Away').update(country=winners[7])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=48,match_choice__home_away='Home').update(country=winners[3])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=48,match_choice__home_away='Away').update(country=winners[1])
            except:
                None

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
            get_winners = [x for x in get_winners if str(x[0].score) != 'None']
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
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=49,match_choice__home_away='Home').update(country=winners[0])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=49,match_choice__home_away='Away').update(country=winners[1])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=50,match_choice__home_away='Home').update(country=winners[2])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=50,match_choice__home_away='Away').update(country=winners[3])
            except:
                None
        
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
            get_winners = [x for x in get_winners if str(x[0].score) != 'None']
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
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=51,match_choice__home_away='Home').update(country=winners[0])
            except:
                None
            try:
                Prediction.objects.filter(user=request.user,match_choice__match_number=51,match_choice__home_away='Away').update(country=winners[1])
            except:
                None


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
            get_winners = [x for x in get_winners if str(x[0].score) != 'None']
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
        check_user_points(request)
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

class HeatView(View):
    template_name = 'predictor/stats/heat_map.html'

    def get(self,request):
        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')
        matches = Match.objects.values()
        actual_id = User.objects.filter(username='Actual_Scores').values()[0]['id']

        predictions = Prediction.objects.values('match_choice__country__name','match_choice__match_number','user')

        
        teams_per_match = [[prediction for prediction in predictions if prediction['match_choice__match_number'] == item['match_number'] and prediction['user'] == actual_id] for item in matches]
        print(teams_per_match)

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
    
class PerPlayerStats(View):
    template_name = 'predictor/stats/per_player.html'
    def get(self,request):

        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon').values()
        groups = Group.objects.values()
        matches = Match.objects.values()
        scores = Prediction.objects.order_by('match_choice__match_number').values('country','match_choice__match_number','match_choice__group','score','user_id','points','exact','actual','user__username')
        stuff = []
        grouped = [[[score for score in scores if score['user_id'] == user['id'] and score['match_choice__match_number'] == event['match_number']] for event in matches] for user in users]
        
        
        for user_choice in grouped:
            user_name = user_choice[0][0]['user__username']
            home_wins = 0
            away_wins = 0
            draws = 0
            a_points = 0
            b_points = 0
            c_points = 0
            d_points = 0
            e_points = 0
            f_points = 0
            finals_points = 0

            for match in user_choice:

                if match[0]['score'] > match[1]['score']:
                    home_wins += 1
                elif match[0]['score'] < match[1]['score']:
                    away_wins += 1 
                else:
                    draws += 1
                try:
                    if match[0]['match_choice__group'] == 1:
                        try:
                            a_points += match[0]['points']
                        except:
                            a_points = a_points
                    elif match[0]['match_choice__group'] == 2:
                        try:
                            b_points += match[0]['points']
                        except:
                            b_points = b_points
                    elif match[0]['match_choice__group'] == 3:
                        try:
                            c_points += match[0]['points']
                        except:
                            c_points = c_points
                    elif match[0]['match_choice__group'] == 4:
                        try:
                            d_points += match[0]['points']
                        except:
                            d_points = d_points
                    elif match[0]['match_choice__group'] == 5:
                        try:
                            e_points += match[0]['points']
                        except:
                            e_points = e_points
                    elif match[0]['match_choice__group'] == 6:
                        try:
                            f_points += match[0]['points']
                        except:
                            f_points = f_points
                except:
                    try:
                        finals_points += match[0]['points']
                    except:
                        finals_points = finals_points

                    
                    
            stuff.append({
                'name':user_name,'home_wins':home_wins,'away_wins':away_wins,'draws':draws,
                'a_points':a_points,'b_points':b_points,'c_points':c_points,'d_points':d_points,
                'e_points':e_points,'f_points':f_points,'finals_points':finals_points,
                'total_points':a_points+b_points+c_points+d_points+e_points+f_points+finals_points,
                'draw_percent':math.ceil((draws/(home_wins+away_wins+draws))*100),
                'home_percent':round((home_wins/(home_wins+away_wins+draws))*100),
                'away_percent':round((away_wins/(home_wins+away_wins+draws))*100),
                          })
        total_h_wins = 0
        total_draw = 0
        total_a_wins = 0
        total_a = 0
        total_b = 0
        total_c = 0
        total_d = 0
        total_e = 0
        total_f = 0
        total_fin = 0
        people = len(stuff)
        for row in stuff:
            total_h_wins += row['home_wins']
            total_draw += row['draws']
            total_a_wins += row['away_wins']
            total_a += row['a_points']
            total_b += row['b_points']
            total_c += row['c_points']
            total_d += row['d_points']
            total_e += row['e_points']
            total_f += row['f_points']
            total_fin += row['finals_points']
        stuff.append({'name':'Total','home_wins':total_h_wins,'away_wins':total_a_wins,'draws':total_draw,
                'a_points':total_a,'b_points':total_b,'c_points':total_c,'d_points':total_d,
                'e_points':total_e,'f_points':total_f,'finals_points':total_fin,
                'total_points':total_a+total_b+total_c+total_d+total_e+total_f+total_fin,
                'draw_percent':math.ceil((total_draw/(total_h_wins+total_a_wins+draws))*100),
                'home_percent':round((total_h_wins/(total_h_wins+total_a_wins+total_draw))*100),
                'away_percent':round((total_a_wins/(total_h_wins+total_a_wins+total_draw))*100),})
        
        stuff.append({'name':'Average','home_wins':round(total_h_wins/people,1),'away_wins':round(total_a_wins/people,1),'draws':round(total_draw/people,1),
                'a_points':round(total_a/people,1),'b_points':round(total_b/people,1),'c_points':round(total_c/people,1),'d_points':round(total_d/people,1),
                'e_points':round(total_e/people,1),'f_points':round(total_f/people,1),'finals_points':round(total_fin/people,1),
                'total_points':round((total_a+total_b+total_c+total_d+total_e+total_f+total_fin)/people,1),
                'draw_percent':math.ceil((total_draw/(total_h_wins+total_a_wins+draws))*100),
                'home_percent':round((total_h_wins/(total_h_wins+total_a_wins+total_draw))*100),
                'away_percent':round((total_a_wins/(total_h_wins+total_a_wins+total_draw))*100),})

        
        context = {
            'stuff':stuff
        }
        return render(request,self.template_name,context)
    
class PerPlayerStats2(View):
    template_name = 'predictor/stats/per_player.html'
    def get(self,request):

        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')
        groups = Group.objects.all()
        matches = Match.objects.all()
        scores = Prediction.objects.order_by('match_choice__match_number').values()
        stuff = []
        grouped = [[[score for score in scores if score['user_id'] == user and score['match_choice_id'] == event]for user in users] for event in matches]
        for user_choice in grouped:
            user_name = user_choice[0][0].user
            home_wins = 0
            away_wins = 0
            draws = 0
            a_points = 0
            b_points = 0
            c_points = 0
            d_points = 0
            e_points = 0
            f_points = 0
            finals_points = 0

            for match in user_choice:

                if match[0]['score'] > match[1]['score']:
                    home_wins += 1
                elif match[0]['score'] < match[1]['score']:
                    away_wins += 1 
                else:
                    draws += 1
                try:
                    if match[0].match_choice.group.id == 1:
                        try:
                            a_points += match[0].points
                        except:
                            a_points = a_points
                    elif match[0].match_choice.group.id == 2:
                        try:
                            b_points += match[0].points
                        except:
                            b_points = b_points
                    elif match[0].match_choice.group.id == 3:
                        try:
                            c_points += match[0].points
                        except:
                            c_points = c_points
                    elif match[0].match_choice.group.id == 4:
                        try:
                            d_points += match[0].points
                        except:
                            d_points = d_points
                    elif match[0].match_choice.group.id == 5:
                        try:
                            e_points += match[0].points
                        except:
                            e_points = e_points
                    elif match[0].match_choice.group.id == 6:
                        try:
                            f_points += match[0].points
                        except:
                            f_points = f_points
                except:
                    try:
                        finals_points += match[0].points
                    except:
                        finals_points = finals_points

                    
                    
            stuff.append({
                'name':user_name,'home_wins':home_wins,'away_wins':away_wins,'draws':draws,
                'a_points':a_points,'b_points':b_points,'c_points':c_points,'d_points':d_points,
                'e_points':e_points,'f_points':f_points,'finals_points':finals_points,
                'total_points':a_points+b_points+c_points+d_points+e_points+f_points+finals_points,
                'draw_percent':math.ceil((draws/(home_wins+away_wins+draws))*100),
                'home_percent':round((home_wins/(home_wins+away_wins+draws))*100),
                'away_percent':round((away_wins/(home_wins+away_wins+draws))*100),
                          })
        total_h_wins = 0
        total_draw = 0
        total_a_wins = 0
        total_a = 0
        total_b = 0
        total_c = 0
        total_d = 0
        total_e = 0
        total_f = 0
        total_fin = 0
        people = len(stuff)
        for row in stuff:
            total_h_wins += row['home_wins']
            total_draw += row['draws']
            total_a_wins += row['away_wins']
            total_a += row['a_points']
            total_b += row['b_points']
            total_c += row['c_points']
            total_d += row['d_points']
            total_e += row['e_points']
            total_f += row['f_points']
            total_fin += row['finals_points']
        stuff.append({'name':'Total','home_wins':total_h_wins,'away_wins':total_a_wins,'draws':total_draw,
                'a_points':total_a,'b_points':total_b,'c_points':total_c,'d_points':total_d,
                'e_points':total_e,'f_points':total_f,'finals_points':total_fin,
                'total_points':total_a+total_b+total_c+total_d+total_e+total_f+total_fin,
                'draw_percent':math.ceil((total_draw/(total_h_wins+total_a_wins+draws))*100),
                'home_percent':round((total_h_wins/(total_h_wins+total_a_wins+total_draw))*100),
                'away_percent':round((total_a_wins/(total_h_wins+total_a_wins+total_draw))*100),})
        
        stuff.append({'name':'Average','home_wins':round(total_h_wins/people,1),'away_wins':round(total_a_wins/people,1),'draws':round(total_draw/people,1),
                'a_points':round(total_a/people,1),'b_points':round(total_b/people,1),'c_points':round(total_c/people,1),'d_points':round(total_d/people,1),
                'e_points':round(total_e/people,1),'f_points':round(total_f/people,1),'finals_points':round(total_fin/people,1),
                'total_points':round((total_a+total_b+total_c+total_d+total_e+total_f+total_fin)/people,1),
                'draw_percent':math.ceil((total_draw/(total_h_wins+total_a_wins+draws))*100),
                'home_percent':round((total_h_wins/(total_h_wins+total_a_wins+total_draw))*100),
                'away_percent':round((total_a_wins/(total_h_wins+total_a_wins+total_draw))*100),})

        
        context = {
            'stuff':stuff
        }
        return render(request,self.template_name,context)
    
class PerMatchStats(View):
    template_name = 'predictor/stats/per_match.html'

    

    def get(self, request):
        context = {
            'matches':'none'
        }

        return render(request,self.template_name,context)
        matches = Match.objects.values()

        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon').values()


        scores = Prediction.objects.select_related().values()#.order_by('match_choice__match_number').values()


        actual_matches = Prediction.objects.order_by('match_choice__match_number').filter(user__username='Actual_Scores').values()
        
        grouped = [[[score for score in scores if score['user_id'] == user['id'] and score['match_choice_id'] == event['id']] for user in users] for event in matches]
        # grouped = [[[print(event) for score in scores]for user in users] for event in matches]
  
        dataset = []
        for index, match in enumerate(grouped):
            temp_total = []
            temp_points = []
            temp_taxi = []
            temp_score = []
           
            for user_pred in match:
                 if str(user_pred[0]['score']) != 'None':
                    if user_pred[0]['score'] > user_pred[1]['score']:
                        win = 1
                        loss = 0
                        draw = 0
                    elif user_pred[0]['score'] < user_pred[1]['score']:
                        win = 0
                        loss = 1
                        draw = 0
                    else:
                        win = 0
                        loss = 0
                        draw = 1
                    if user_pred[0]['points']:
                        points = user_pred[0]['points']
                    else:
                        points = 0
                    datarow = [win,loss,draw,user_pred[0]['score'],user_pred[1]['score'],points]
                    temp_total.append(datarow)
                    if user_pred[0]['points'] == 0:
                        wrong = 1
                        right = 0
                        gd = 0
                        exact = 0
                    elif user_pred[0]['points'] == 1:
                        wrong = 0
                        right = 1
                        gd = 0
                        exact = 0
                    elif user_pred[0]['points'] == 2:
                        wrong = 0
                        right = 0
                        gd = 1
                        exact = 0
                    elif user_pred[0]['points'] == 4:
                        wrong = 0
                        right = 0
                        gd = 0
                        exact = 1
                    else:
                        wrong = 0
                        right = 0
                        gd = 0
                        exact = 0
                    temp_points.append([wrong,right,gd,exact])
                    # if Prediction.objects.filter(user__username='Actual_Scores',match_choice=user_pred[0]['match_choice_id']).values()[0]['score'] != None:
                    #     x = abs(Prediction.objects.filter(user__username='Actual_Scores',match_choice=user_pred[0]['match_choice_id']).values()[0]['score'] - user_pred[0]['score'])
                    #     y = abs(Prediction.objects.filter(user__username='Actual_Scores',match_choice=user_pred[1]['match_choice_id']).values()[0]['score'] - user_pred[1]['score'])
                    #     taxi_diff = x+y
                    #     temp_taxi.append(taxi_diff)
                    # temp_score.append([user_pred[0]['score'],user_pred[1]['score']])

            points_row = [sum(col) for col in zip(*temp_points)]
            avg = [round(float(sum(col))/len(col)*100) for col in zip(*temp_total)]
            avg_score = [round(float(sum(col))/len(col),2) for col in zip(*temp_score)]
            # try:
            #     avg_taxi = round(sum(temp_taxi)/len(temp_taxi),2)
            # except:
            #     avg_taxi = ''
            # dataset.append([avg,[actual_matches[index*2],actual_matches[index*2+1]],points_row,avg_taxi,avg_score])
            dataset.append([avg,[actual_matches[index*2],actual_matches[index*2+1]],points_row,'hi',avg_score])

        context = {
            'matches':dataset
        }

        return render(request,self.template_name,context)
    
class ThirdPlaceStats(View):

    template_name = 'predictor/stats/third_place.html'

    def get_user_third_teams(self,user_name,matches,groups):
        scores = Prediction.objects.filter(user__username=user_name).order_by('match_choice__match_number')
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
        return(best_thirds)
    
    def get(self,request):
        groups = Group.objects.all()
        matches = Match.objects.all()
        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')
        user_list = [item.username for item in users]
        print(user_list)
        third_teams = [[self.get_user_third_teams(item,matches,groups),item] for item in user_list]
        actual_third = [self.get_user_third_teams('Actual_Scores',matches,groups),'Actual_Scores']
        
        
        


        context = {
            'third_teams':third_teams,
            'actual_third':actual_third,
            }
        return render(request,self.template_name,context)
    

class TestStats(View):
    template_name = 'predictor/stats/per_match.html'

    

    def get(self, request):
        
        matches = Match.objects.all()
        users = User.objects.exclude(username='Actual_Scores').exclude(username='richardlongdon')


        scores = Prediction.objects.order_by('match_choice__match_number').values()         

        actual_matches = Prediction.objects.order_by('match_choice__match_number').filter(user__username='Actual_Scores').all()
        
        

        grouped = [[[score for score in scores if score['user_id'] == user and score['match_choice_id'] == event]for user in users] for event in matches]
        # grouped = [[[print(score) for score in scores] for user in users] for event in matches]
        
        grouped = []
        
        
        context = {
            'grouped':grouped
        }

        return render(request,self.template_name,context)