# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-21 19:19
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.TextField(db_index=True, help_text='The organization code', unique=True)),
                ('long_description', models.TextField(help_text='Long-format description of the organization')),
                ('short_description', models.TextField(help_text='Short-format description of the organization')),
                ('is_bureau', models.BooleanField(default=False, help_text='Boolean indicator if this organization is a bureau')),
                ('_parent_organization_code', models.TextField(help_text='Organization Code of the parent Organization', null=True)),
                ('_parent_bureau_code', models.TextField(help_text='Bureau Code of the parent parent Bureau', null=True)),
                ('bureau_organization', models.ForeignKey(help_text='The parent Bureau for this organization', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='bureau_children', to='organization.Organization')),
                ('parent_organization', models.ForeignKey(help_text='The parent organization of this organization', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='organizion_children', to='organization.Organization')),
            ],
        ),
    ]