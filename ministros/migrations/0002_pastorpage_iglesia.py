# Generated by Django 3.0.5 on 2020-09-17 13:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('iglesias', '0003_auto_20200916_0533'),
        ('ministros', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pastorpage',
            name='iglesia',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='iglesias.IglesiaPage'),
        ),
    ]