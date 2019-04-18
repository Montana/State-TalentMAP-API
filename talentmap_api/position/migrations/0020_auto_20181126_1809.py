# Generated by Django 2.0.4 on 2018-11-26 18:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bidding', '0010_biddingstatus'),
        ('position', '0019_auto_20181126_1619'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalposition',
            name='latest_bidcycle',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='bidding.BidCycle'),
        ),
        migrations.AddField(
            model_name='position',
            name='latest_bidcycle',
            field=models.OneToOneField(help_text='The latest bid cycle this position is in', null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='latest_cycle_for_positions', to='bidding.BidCycle'),
        ),
    ]