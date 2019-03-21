# Generated by Django 2.0.4 on 2019-03-21 13:03

from django.db import migrations, models

import random

class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0004_auto_20180409_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='emp_id',
            field=models.TextField(default=f"{random.randint(1000, 10000)}", help_text="The user's employee id"),
            preserve_default=False,
        ),
    ]
