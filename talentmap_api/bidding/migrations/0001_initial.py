# Generated by Django 2.0.13 on 2020-05-29 17:18

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_string_representation', models.CharField(blank=True, help_text='The string representation of this object', max_length=255, null=True)),
            ],
            options={
                'managed': False,
            },
        ),
    ]
