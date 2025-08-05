Usage Guide
===========

In Your Models
--------------

Use the ``EditorJSField`` in your models as you would any other Django model field. It stores the editor's content as JSON.

- **To use a custom set of Editor.js tools for a field**, pass a ``tools`` dictionary to the field.
- **To use the global (default) tool configuration**, define the field without the ``tools`` argument.

Since ``EditorJSField`` inherits from Django's ``models.JSONField``, you can also pass any of its standard attributes, such as ``blank=True`` or ``null=True``.

Example:

.. code-block:: python

    # my_app/models.py
    from django.db import models
    from editor_js.fields import EditorJSField

    class Post(models.Model):
        title = models.CharField(max_length=200)
        
        # This field will only have Header and List tools
        summary = EditorJSField(tools={
            'header': {
                'class': 'Header',
                'script': 'https://cdn.jsdelivr.net/npm/@editorjs/header@latest',
            },
            'list': {
                'class': 'EditorjsList',
                'script': 'https://cdn.jsdelivr.net/npm/@editorjs/list@latest',
            }
        })

        # This field will use the default or global tool configuration
        body = EditorJSField()

The field will automatically render the iframe widget in the Django admin.


Rendering Content in Templates
------------------------------

The library includes a built-in template filter to easily render your ``EditorJSField`` data as HTML.

1. **Load the filter** in your template:

.. code-block:: django

    {% load editor_js_filters %}

2. **Apply the filter** to your field's data:

.. code-block:: django

    <!-- post_detail.html -->
    {% load editor_js_filters %}

    <article>
        <h1>{{ post.title }}</h1>
        <div class="content">
            {{ post.body|render_editor_js }}
        </div>
    </article>

