# Generated by Django 2.0.4 on 2019-07-22 18:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bidding', '0017_auto_20190611_1912'),
    ]

    operations = [
        migrations.AddField(
            model_name='cycleposition',
            name='is_hard_to_fill',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cycleposition',
            name='is_urgent_vacancy',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='cycleposition',
            name='is_volunteer',
            field=models.BooleanField(default=False),
        ),
    ]
