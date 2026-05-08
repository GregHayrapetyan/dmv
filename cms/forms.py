from django.core.exceptions import ValidationError
from wagtail.images.forms import BaseImageForm


class RestrictedImageForm(BaseImageForm):
    """
    Custom Wagtail image form base.
    Only allows WebP uploads.
    Large images are auto-resized to max IMAGE_MAX_DIMENSION px
    by the post_save signal in cms.signals.
    """

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file and hasattr(file, 'name'):
            if not file.name.lower().endswith('.webp'):
                raise ValidationError(
                    'Only WebP images are allowed. '
                    'Please convert your image to .webp format before uploading.'
                )
        return file
