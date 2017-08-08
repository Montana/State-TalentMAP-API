# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-03 18:52
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0006_auto_20170803_1819'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='location',
            field=models.ForeignKey(help_text='The location of the post', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='posts', to='organization.Location'),
        ),
    ]