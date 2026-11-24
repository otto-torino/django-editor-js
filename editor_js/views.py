import json
import os

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.utils import translation
from django.utils.module_loading import import_string
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_POST

from .config import get_editor_js_config, get_editor_js_storage
from .i18n import get_editor_js_i18n


def _requested_language(request):
    """
    The language the widget asks for, the one of the page around the iframe,
    when the project has it; otherwise None, and the language of the request.
    """
    language = request.GET.get('lang')
    if not language:
        return None
    try:
        return translation.get_supported_language_variant(language)
    except LookupError:
        return None


@xframe_options_sameorigin
def editor_js_iframe_view(request):
    origin = f"{request.scheme}://{request.get_host()}"
    csrf_token = get_token(request)

    config = get_editor_js_config()
    tools_config = config.get('TOOLS', {})
    css_files = config.get('CSS_FILES', [])

    language = _requested_language(request) or translation.get_language()
    with translation.override(language):
        return render(request, 'editor_js/editor_js_iframe.html', {
            "trusted_origin": origin,
            "upload_image_url": reverse('editor_js_image_upload'),
            "csrf_token": csrf_token,
            "css_files": css_files,
            "tools_config": tools_config,
            "tools_json": json.dumps(tools_config),
            "i18n_json": json.dumps(get_editor_js_i18n()),
        })


def can_upload_images(request):
    """
    The default rule of ``EDITOR_JS["IMAGE_UPLOAD_PERMISSION"]``: only the
    active staff users, the ones that edit the content in the admin.
    """
    user = getattr(request, 'user', None)
    return bool(user and user.is_active and user.is_staff)


def _get_upload_permission():
    path = get_editor_js_config().get('IMAGE_UPLOAD_PERMISSION')
    return import_string(path) if path else can_upload_images


def _detect_image_extension(uploaded_file):
    """
    The extension of the image format found in the first bytes of the file,
    or None: the content type and the name come from the client.
    """
    head = uploaded_file.read(12)
    uploaded_file.seek(0)
    if head.startswith(b'\xff\xd8\xff'):
        return 'jpg'
    if head.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'png'
    if head[:6] in (b'GIF87a', b'GIF89a'):
        return 'gif'
    if head[:4] == b'RIFF' and head[8:12] == b'WEBP':
        return 'webp'
    return None


def _pillow_accepts(uploaded_file):
    """Whether Pillow, when installed, can read the whole image."""
    try:
        from PIL import Image
    except ImportError:
        return True
    try:
        Image.open(uploaded_file).verify()
    except Exception:
        return False
    finally:
        uploaded_file.seek(0)
    return True


@require_POST
def image_upload_view(request):
    """
    Saves an image of the Editor.js image tool in the storage of the library.

    The request must carry the CSRF token, which the editor sends in the
    X-CSRFToken header, and come from a user allowed by
    ``EDITOR_JS["IMAGE_UPLOAD_PERMISSION"]`` (the active staff users by
    default). The file must be a JPEG, PNG, GIF or WebP image: it is saved with
    the extension of its format, whatever its name.
    """
    if not _get_upload_permission()(request):
        return JsonResponse(
            {'success': 0, 'message': 'You are not allowed to upload images.'},
            status=403,
        )

    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'success': 0, 'message': 'No image provided.'}, status=400)

    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if image_file.content_type not in allowed_types:
        return JsonResponse({
            'success': 0,
            'message': f'Invalid file type: {image_file.content_type}.'
        }, status=400)

    extension = _detect_image_extension(image_file)
    if not extension or not _pillow_accepts(image_file):
        return JsonResponse({'success': 0, 'message': 'Invalid image file.'}, status=400)

    stem = os.path.splitext(os.path.basename(image_file.name))[0] or 'image'
    storage = get_editor_js_storage()
    file_name = storage.save(f'editor_js/{stem}.{extension}', image_file)
    file_url = storage.url(file_name)

    return JsonResponse({
        'success': 1,
        'file': {
            'url': file_url,
        }
    })
