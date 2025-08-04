from django.urls import path
from .views import editor_js_iframe_view, image_upload_view

urlpatterns = [
    path('', editor_js_iframe_view, name='editor_js_iframe'),
    path('editor-js-image-upload/', image_upload_view, name='editor_js_image_upload'),
]