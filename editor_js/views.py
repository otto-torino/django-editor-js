import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.urls import reverse
from django.middleware.csrf import get_token 
from django.conf import settings
from .utils import get_editorjs_storage, get_editorjs_config

@xframe_options_sameorigin
def editorjs_iframe_view(request):
    origin = f"{request.scheme}://{request.get_host()}"
    csrf_token = get_token(request)

    config = get_editorjs_config()
    tools_config = config.get('TOOLS', {})
    css_file = config.get('CSS_FILE')

    return render(request, 'editor_js/editorjs_iframe.html', {
        "trusted_origin": origin,
        "upload_image_url": reverse('editorjs_image_upload'),
        "csrf_token": csrf_token,
        "custom_css_file": css_file,
        "tools_config": tools_config, 
        "tools_json": json.dumps(tools_config)
    })

@csrf_exempt
def image_upload_view(request):
    if request.method == 'POST' and request.FILES.get('image'):

        storage = get_editorjs_storage()

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
