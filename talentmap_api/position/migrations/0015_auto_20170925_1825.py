# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-25 18:25
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('position', '0014_auto_20170912_2139'),
    ]

    operations = [
        migrations.AddField(
            model_name='capsuledescription',
            name='point_of_contact',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='capsuledescription',
            name='website',
            field=models.TextField(null=True),
        ),
    ]