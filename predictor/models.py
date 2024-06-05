from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Country(models.Model):
    name = models.CharField(max_length=28)
    fifa_ranking = models.IntegerField()
    fifa_points = models.DecimalField(decimal_places=1,max_digits=6)
    short_name = models.CharField(max_length=23)

    class Meta:
        verbose_name_plural = "countries"

    def __str__(self) -> str:
        return f'{self.name} - {self.short_name}'

class Group(models.Model):
    letter = models.CharField(max_length=1)

    def __str__(self) -> str:
        return f'Group {self.letter}'


class Match(models.Model):
    country = models.ForeignKey(Country,on_delete=models.CASCADE,blank=True,null=True)
    date = models.DateTimeField()
    match_number = models.IntegerField()
    stage = models.CharField(max_length=20)
    home_away = models.CharField(max_length=20)
    location = models.CharField(max_length=50,default=None,null=True)
    group = models.ForeignKey(Group, verbose_name=("Group"),on_delete=models.CASCADE,default=None,null=True,blank=True)

    class Meta:
        verbose_name_plural = "matches"

    def __str__(self) -> str:
        try:
            name = f'Match {self.match_number} {self.country.short_name}'
        except:
            name = f'Match {self.match_number}'
        return name

class Prediction(models.Model):
    match_choice = models.ForeignKey(Match,on_delete=models.CASCADE)
    score = models.IntegerField(null=True)
    score_aet = models.IntegerField(null=True)
    penalties = models.IntegerField(null=True)
    result = models.CharField(max_length=30,null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user}: {self.match_choice}'
    

