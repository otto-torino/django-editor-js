Installation
============

1. Install the package from PyPI:

.. code-block:: bash

   pip install dj-editor-js

2. Add ``editor_js`` to your ``INSTALLED_APPS`` in ``settings.py``:

.. code-block:: python

   # settings.py
   INSTALLED_APPS = [
       # ...
       'editor_js',
   ]

3. Include the library's URLs in your project's ``urls.py``. These are required for the iframe and the image upload endpoint.

.. code-block:: python

    # your_project/urls.py
    from django.urls import path, include

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('editor-js/', include('editor_js.urls')),
        # ... your other urls
    ]
