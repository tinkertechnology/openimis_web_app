# Generated by Django 2.1.14 on 2021-06-10 20:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0007_voucherpayment'),
    ]

    operations = [
        migrations.AddField(
            model_name='voucherpayment',
            name='vocher_id',
            field=models.CharField(default='20210610201821', max_length=50),
        ),
    ]
