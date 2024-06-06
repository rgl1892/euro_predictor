from django.contrib import admin
from .models import Country,Group, Score,Prediction,Match

# Register your models here.
class ScoreAdmin(admin.ModelAdmin):
    list_display = ["__str__","id","match_number"]

class CountryAdmin(admin.ModelAdmin):
    list_display = ["__str__","id"]

class GroupAdmin(admin.ModelAdmin):
    list_display = ["__str__","id"]

class MatchAdmin(admin.ModelAdmin):
    list_display = ["__str__","id"]

admin.site.register(Score, ScoreAdmin)
admin.site.register(Country,CountryAdmin)
admin.site.register(Group,GroupAdmin)
admin.site.register(Prediction)
admin.site.register(Match,MatchAdmin)