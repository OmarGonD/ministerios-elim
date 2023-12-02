from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

'''El poder del cotenido en bloques es que lo pueden mover de arriba a abajo dentro del loop '''

class TitleAndTextBlock(blocks.StructBlock):

    title = blocks.CharBlock(required=True, help_text='Ingrese un título')
    text = blocks.TextBlock(required=True, help_text='Añade texto adicional')

    class Meta:
        template = "streams/title_and_text_block.html"
        icon = 'edit'
        label = "Title & Text"


class CardBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=True, help_text="Agrega el título")

    cards = blocks.ListBlock(
        blocks.StructBlock(
            [
                ("image", ImageChooserBlock(required=True)),
                ("title", blocks.CharBlock(required=True, max_length=50)),
                ("text", blocks.TextBlock(required=True, max_length=200)),
                ("button_page", blocks.PageChooserBlock(required=False)),
                ("button_url", blocks.URLBlock(required=False, help_text="Si el botón de page está habilidado, usará ese"))
            ]
        )
    )

    class Meta:
        template = "streams/card_block.html"
        icon = "placeholder"
        label = "Full RichText"

class RichtextBlock(blocks.RichTextBlock):
    '''A diferencia del struckBlock, RichTextBlock no estructura el texto como un bloque, sino que
    devuelve lo que se indica al agregar contenido al editar.'''
    class Meta:
        template = "streams/richtext_block.html"
        icon = "doc-full"
        label = "Full RichText"


class SimpleRichtextBlock(blocks.RichTextBlock):
    '''A diferencia del struckBlock, RichTextBlock no estructura el texto como un bloque, sino que
    devuelve lo que se indica al agregar contenido al editar.'''

    def __init__(self, required=True, help_text=None, editor='default', features=None, validators=(), **kwargs):
        super().__init__(**kwargs)
        self.features = ['bold', 'italic', 'link']
        
    '''Usamos el mismo tempalte porque nada cambia, básicamente son lo mismo, sin todas las funciones'''    
    class Meta:
        template = "streams/richtext_block.html"
        icon = "edit"
        label = "Simple RichText"        


class CTABlock(blocks.StructBlock):
    """A single ..."""
    title = blocks.CharBlock(required=True, max_length=60)
    text = blocks.RichTextBlock(required=True, features=["bold", "italic"])
    button_page = blocks.PageChooserBlock(required=False)
    button_url = blocks.URLBlock(required=True)
    button_text = blocks.CharBlock(required=True, default="Conoce más", max_length=400)

    class Meta:
        template = "streams/cta_block.html"
        icon = "placeholder"
        label = "Call to action"   