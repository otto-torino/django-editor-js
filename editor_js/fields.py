from django.db import models
from django.db.models.signals import post_delete
from urllib.parse import unquote

from .widgets import EditorJsIframeWidget
from .config import get_editor_js_storage


def _delete_editor_js_images_on_delete(sender, instance, **kwargs):
    """
    Deletes all images used in all EditorJS fields of the given instance.

    This function is meant to be used as a post_delete signal handler.
    """
    for field in sender._meta.get_fields():
        if isinstance(field, EditorJSField):
            data = getattr(instance, field.attname, None)
            if not data:
                continue

            urls_to_delete = field._extract_image_urls(data)
            storage = get_editor_js_storage()
            base_url = getattr(storage, "base_url", None)

            if not base_url:
                continue

            for url in urls_to_delete:
                if url.startswith(base_url):
                    relative_path = url.replace(base_url, "", 1).lstrip("/")
                    decoded_path = unquote(relative_path)
                    try:
                        if storage.exists(decoded_path):
                            storage.delete(decoded_path)
                    except Exception as e:
                        print(f"Error deleting file on instance delete: {e}")


class EditorJSField(models.JSONField):
    """
    A JSONField that stores Editor.js data. It deletes the images used in the
    Editor.js data when the instance is deleted.
    """

    def __init__(self, *args, **kwargs):
        """
        :param tools: A dictionary with a specific tool configuration for this field,
                      overriding the global settings.
        """
        self.tools = kwargs.pop("tools", None)
        super().__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        """
        Return a form field for the Editor.js data.
        """
        config = {}
        if self.tools:
            config['tools'] = self.tools
        
        kwargs["widget"] = EditorJsIframeWidget(attrs={"config": config})
        return super().formfield(**kwargs)

    def contribute_to_class(self, cls, name, **kwargs):
        """
        Connect a post_delete signal to the model class to delete the images
        used in the Editor.js data when the instance is deleted.
        """
        super().contribute_to_class(cls, name, **kwargs)
        if not hasattr(cls, "_editor_js_delete_signal_connected"):
            post_delete.connect(
                _delete_editor_js_images_on_delete, sender=cls, weak=False
            )
            cls._editor_js_delete_signal_connected = True

    def _extract_image_urls(self, data):
        """
        Extract the URLs of the images used in the Editor.js data.
        """
        image_urls = []
        if not isinstance(data, dict) or "blocks" not in data:
            return image_urls
        for block in data.get("blocks", []):
            if block.get("type") == "image":
                file_data = block.get("data", {}).get("file", {})
                url = file_data.get("url")
                if url:
                    image_urls.append(url)
        return image_urls

    def pre_save(self, model_instance, add):
        """
        Delete the images that are no longer used in the Editor.js data when
        the instance is saved.
        """
        new_value = super().pre_save(model_instance, add)
        old_value = None
        if model_instance.pk:
            try:
                old_instance = model_instance.__class__.objects.get(
                    pk=model_instance.pk
                )
                old_value = getattr(old_instance, self.attname)
            except model_instance.__class__.DoesNotExist:
                pass

        old_image_urls = set(self._extract_image_urls(old_value))
        new_image_urls = set(self._extract_image_urls(new_value))
        urls_to_delete = old_image_urls - new_image_urls

        if urls_to_delete:
            storage = get_editor_js_storage()
            base_url = getattr(storage, "base_url", None)

            if base_url:
                for url in urls_to_delete:
                    if url.startswith(base_url):
                        relative_path = url.replace(base_url, "", 1).lstrip("/")
                        decoded_path = unquote(relative_path)
                        try:
                            if storage.exists(decoded_path):
                                storage.delete(decoded_path)
                        except Exception as e:
                            print(f"Error deleting orphaned file: {e}")
        return new_value
