from django.db import migrations


def forwards_func(apps, schema_editor):
    UserProfile = apps.get_model('home', 'UserProfile')
    UserProfile.objects.filter(role='pastor').update(role='pastor_elim')


def reverse_func(apps, schema_editor):
    UserProfile = apps.get_model('home', 'UserProfile')
    UserProfile.objects.filter(role='pastor_elim').update(role='pastor')


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0003_userprofile'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
