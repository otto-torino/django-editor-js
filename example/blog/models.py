from django.db import models
from editor_js.fields import EditorJSField

class Post(models.Model):
    title = models.CharField(max_length=200)
    body = EditorJSField()

    def __str__(self):
        return self.title
