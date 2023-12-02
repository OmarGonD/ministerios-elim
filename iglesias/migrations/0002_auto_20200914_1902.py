# Generated by Django 3.0.5 on 2020-09-15 00:02

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.contrib.taggit


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('taggit', '0003_taggeditem_add_unique_index'),
        ('iglesias', '0001_initial'),
        ('wagtailimages', '0022_uploadedimage'),
        ('ministros', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='iglesiapage',
            name='pastor',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='ministros.PastorPage'),
        ),
        migrations.AddField(
            model_name='iglesiaeventospage',
            name='event_image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='wagtailimages.Image'),
        ),
        migrations.AddField(
            model_name='iglesiaeventospage',
            name='tags',
            field=modelcluster.contrib.taggit.ClusterTaggableManager(blank=True, help_text='A comma-separated list of tags.', through='iglesias.IglesiaPageTag', to='taggit.Tag', verbose_name='Tags'),
        ),
    ]
