Usage Guide
===========

In Your Models
--------------

Use the ``EditorJSField`` in your models just like any other field. It stores the editor's output as JSON.

.. code-block:: python

    # my_app/models.py
    from django.db import models
    from editor_js.fields import EditorJSField

    class Post(models.Model):
        title = models.CharField(max_length=200)
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

