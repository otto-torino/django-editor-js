from django.test import TestCase
from django.urls import reverse

class ViewsTest(TestCase):
    def test_iframe_view(self):
        url = reverse('editor_js_iframe')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'editor_js/editor_js_iframe.html')

    def test_image_upload_view_get(self):
        url = reverse('editor_js_image_upload')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'success': 0})
