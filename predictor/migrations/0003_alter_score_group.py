# Generated by Django 4.2.4 on 2024-06-09 21:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('predictor', '0002_prediction_country_alter_score_group'),
    ]

    operations = [
        migrations.AlterField(
            model_name='score',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='predictor.group', verbose_name='Group'),
        ),
    ]
