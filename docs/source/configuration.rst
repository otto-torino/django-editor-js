Configuration
=============

You can customize the library by adding an ``EDITOR_JS`` dictionary to your ``settings.py``. If you don't provide this, the library will use its sensible defaults.

.. code-block:: python

    # settings.py
    EDITOR_JS = {
        # Define a custom storage backend for uploaded images.
        "STORAGE_BACKEND": "app.storage.PrivateMediaStorage",

        # Specify the custom CSS files to be loaded inside the editor's iframe.
        "CSS_FILES": ["my_app/css/style.css", "other_app/css/style.css"],
        
        # Specify a custom Python class to render the JSON data to HTML.
        "RENDERER_CLASS": "my_app.renderers.MyCustomRenderer",

        # Who may upload images: a callable taking the request and returning a
        # boolean. By default only the active staff users may upload.
        "IMAGE_UPLOAD_PERMISSION": "my_app.permissions.can_upload_images",
        
        # Configure the tools available to the editor.
        "TOOLS": {
            # Add a new custom tool
            'my_custom_tool': {
                'class': 'MyCustomTool',
                'script': 'my_app/js/my-custom-tool.js',
                'static': True,
                'config': {
                    'placeholder': 'Enter your custom text...'
                }
            },
            # Remove a default tool
            'quote': None,
        }
    }

Image uploads
-------------

The image tool posts its files to the ``editor_js_image_upload`` view, which:

- accepts only ``POST`` requests carrying the CSRF token (the editor sends it in the ``X-CSRFToken`` header);
- accepts only the users allowed by ``IMAGE_UPLOAD_PERMISSION``, the active staff users by default (``editor_js.views.can_upload_images``);
- accepts only JPEG, PNG, GIF and WebP images, recognised from the bytes of the file (and read whole by Pillow when it is installed), not from the content type or the name sent by the client;
- saves each image under ``editor_js/`` in the configured storage, with the extension of its format.
