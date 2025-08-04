import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.urls import reverse
from django.middleware.csrf import get_token 
from django.conf import settings
from .config import get_editor_js_storage, get_editor_js_config

@xframe_options_sameorigin
def editor_js_iframe_view(request):
    origin = f"{request.scheme}://{request.get_host()}"
    csrf_token = get_token(request)

    config = get_editor_js_config()
    tools_config = config.get('TOOLS', {})
    css_file = config.get('CSS_FILE')

    print(f"[DjangoEditorJSIframe] Loaded with config: {tools_config}")

    return render(request, 'editor_js/editor_js_iframe.html', {
        "trusted_origin": origin,
        "upload_image_url": reverse('editor_js_image_upload'),
        "csrf_token": csrf_token,
        "custom_css_file": css_file,
        "tools_config": tools_config, 
        "tools_json": json.dumps(tools_config)
    })

@csrf_exempt
def image_upload_view(request):
    if request.method == 'POST' and request.FILES.get('image'):

        storage = get_editor_js_storage()

        image_file = request.FILES['image']
        file_name = storage.save(f'editor_js/{image_file.name}', image_file)
        file_url = storage.url(file_name)
        
        return JsonResponse({
            'success': 1,
            'file': {
                'url': file_url,
            }
        })
    return JsonResponse({'success': 0})
