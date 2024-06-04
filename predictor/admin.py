from django.contrib import admin
from .models import Country,Group, Match,Prediction

# Register your models here.

admin.site.register(Match)
admin.site.register(Country)
admin.site.register(Group)
admin.site.register(Prediction)