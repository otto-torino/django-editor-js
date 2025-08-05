from django.db import models
from editor_js.fields import EditorJSField

class Post(models.Model):
    title = models.CharField(max_length=200)

    # This field will only have Header and List tools
    summary = EditorJSField(
        blank=True,
        # Specific tools configuration for this field
        tools={
            'header': {
                'class': 'Header',
                'script': 'https://cdn.jsdelivr.net/npm/@editorjs/header@latest',
            },
            'list': {
                'class': 'EditorjsList',
                'script': 'https://cdn.jsdelivr.net/npm/@editorjs/list@latest',
            }
        }
    )

    # This field will use the default or global tool configuration
    body = EditorJSField(blank=True)

    def __str__(self):
        return self.title
