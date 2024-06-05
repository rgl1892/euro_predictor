from django import forms
from .models import *
from django.contrib.auth.forms import AuthenticationForm,UserCreationForm
from django.contrib.auth import password_validation


class EditAuthForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

class EditUserForm(UserCreationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password1 = forms.CharField(help_text=password_validation.password_validators_help_text_html(),label=("Password"),widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder':'Password'}))
    password2 = forms.CharField(label=("Re-enter Password"),widget=forms.PasswordInput(attrs={'class': 'form-control','placeholder':'Password'}))
