# Generated by Django 3.0.5 on 2020-09-21 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0002_auto_20200914_2012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='reference',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
