from django.shortcuts import render
from django.views.generic import View
from .models import Country,Group,Match,Prediction

class Home(View):

    template_name = 'predictor/home.html'

    def get(self, request):
        countries = Country.objects.order_by('fifa_ranking')
        context = {
            'countries':countries
        }
        return render(request, self.template_name, context)


# Create your views here.
