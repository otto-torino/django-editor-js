from django.urls import path
from.views import editorjs_iframe_view, image_upload_view

urlpatterns = [
    path('', editorjs_iframe_view, name='editorjs_iframe'),
    path('editorjs-image-upload/', image_upload_view, name='editorjs_image_upload'),
]