# Generated by Django 3.0.14 on 2021-06-01 23:13

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0005_healthfacilitycatchment_healthfacilitylegalform_healthfacilitymutation_healthfacilitysublevel'),
        ('webapp', '0005_auto_20210530_2156'),
    ]

    operations = [
        migrations.CreateModel(
            name='HealthFacilityCoordinate',
            fields=[
                ('id', models.AutoField(db_column='hfcId', primary_key=True, serialize=False)),
                ('uuid', models.CharField(db_column='hfcUUID', default=uuid.uuid4, max_length=36, unique=True)),
                ('latitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('longitude', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('health_facility', models.ForeignKey(db_column='HFID', on_delete=django.db.models.deletion.DO_NOTHING, to='location.HealthFacility')),
            ],
        ),
    ]