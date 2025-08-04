from django.db import models
from editor_js.fields import EditorJSField

class Post(models.Model):
    title = models.CharField(max_length=100)
    content = EditorJSField()
    