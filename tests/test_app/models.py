from django.db import models
from editor_js.fields import EditorJSField

class Post(models.Model):
    title = models.CharField(max_length=100)
    summary = EditorJSField(
        blank=True,
        null=True,
        tools = {
            'header': {
                'class': 'MyCustomHeader',
                'script': 'path/to/my/custom/header.js'
            },
            'alert': {
                'class': 'AlertTool',
                'script': 'path/to/alert.js'
            }
        }
    )
    content = EditorJSField(blank=True, null=True)
    