from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError

from .forms import EditAuthForm,EditUserForm
from .models import Country,Group,Match,Prediction


class Home(View):

    template_name = 'predictor/home.html'

    def get(self, request):
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
