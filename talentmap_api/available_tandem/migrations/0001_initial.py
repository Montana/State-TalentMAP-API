# Generated by Django 2.0.13 on 2020-09-25 15:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('user_profile', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableFavoriteTandem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('_string_representation', models.CharField(blank=True, help_text='The string representation of this object', max_length=255, null=True)),
                ('cp_id', models.CharField(max_length=255)),
                ('archived', models.BooleanField(default=False)),
                ('user', models.ForeignKey(help_text='The user to which this tandem favorite belongs', on_delete=django.db.models.deletion.DO_NOTHING, to='user_profile.UserProfile')),
            ],
            options={
                'ordering': ['cp_id'],
                'managed': True,
            },
        ),
        migrations.AlterUniqueTogether(
            name='availablefavoritetandem',
            unique_together={('cp_id', 'user')},
        ),
    ]