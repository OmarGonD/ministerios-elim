# Generated by Django 3.0.5 on 2020-09-15 00:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import ministros.models
import streams.blocks
import wagtail.blocks
import wagtail.fields
import wagtail.images.blocks


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0045_assign_unlock_grouppagepermission'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PastorPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('content', wagtail.fields.StreamField([('title_and_text', wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(help_text='Ingrese un título', required=True)), ('text', wagtail.blocks.TextBlock(help_text='Añade texto adicional', required=True))], classname='text_and_title')), ('full_richtext', streams.blocks.RichtextBlock()), ('simple_richtext', streams.blocks.SimpleRichtextBlock()), ('cards', wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(help_text='Agrega el título', required=True)), ('cards', wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([('image', wagtail.images.blocks.ImageChooserBlock(required=True)), ('title', wagtail.blocks.CharBlock(max_length=50, required=True)), ('text', wagtail.blocks.TextBlock(max_length=200, required=True)), ('button_page', wagtail.blocks.PageChooserBlock(required=False)), ('button_url', wagtail.blocks.URLBlock(help_text='Si el botón de page está habilidado, usará ese', required=False))])))])), ('cta', wagtail.blocks.StructBlock([('title', wagtail.blocks.CharBlock(max_length=60, required=True)), ('text', wagtail.blocks.RichTextBlock(features=['bold', 'italic'], required=True)), ('button_page', wagtail.blocks.PageChooserBlock(required=False)), ('button_url', wagtail.blocks.URLBlock(required=True)), ('button_text', wagtail.blocks.CharBlock(default='Conoce más', max_length=400, required=True))]))], blank=True, null=True)),
                ('user', models.ForeignKey(on_delete=models.SET(ministros.models.get_sentinel_user), related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Pastor',
                'verbose_name_plural': 'Pastores',
            },
            bases=('wagtailcore.page',),
        ),
    ]
