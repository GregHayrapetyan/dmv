from wagtail.images.forms import BaseImageForm


class RestrictedImageForm(BaseImageForm):
    """
    Custom Wagtail image form base.
    Large images are auto-resized to max IMAGE_MAX_DIMENSION px
    by the post_save signal in cms.signals.
    """
    pass
