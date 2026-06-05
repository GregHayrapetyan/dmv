"""
Translation utilities for API responses.

Provides a mixin for DRF serializers to return translated field values
based on the 'lang' query parameter.

Supported languages: en (default), ru, hy, hi, es, zh
"""

SUPPORTED_LANGUAGES = ['en', 'ru', 'hy', 'hi', 'es', 'zh']


def get_translated_value(obj, field_name, lang):
    """
    Get the translated value for a field based on language.
    
    Falls back to the default (English) field if translation is empty.
    
    Args:
        obj: Model instance
        field_name: Base field name (e.g., 'title', 'description')
        lang: Language code (e.g., 'ru', 'hy', 'es')
    
    Returns:
        Translated field value or default value
    """
    if lang and lang != 'en' and lang in SUPPORTED_LANGUAGES:
        translated_field = f"{field_name}_{lang}"
        if hasattr(obj, translated_field):
            translated_value = getattr(obj, translated_field, None)
            if translated_value:  # Return translation if not empty
                return translated_value
    
    # Return default (English) value
    return getattr(obj, field_name, None)


class TranslatedSerializerMixin:
    """
    Mixin for DRF serializers to support language-based field translations.
    
    Usage:
        1. Add this mixin to your serializer class
        2. Define `translated_fields` as a list of field names that have translations
        3. The serializer will automatically return translated values based on
           the 'lang' query parameter in the request
    
    Example:
        class MySerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
            translated_fields = ['title', 'description']
            
            class Meta:
                model = MyModel
                fields = ['id', 'title', 'description']
    
    The frontend can request translations by adding ?lang=ru (or hy, hi, es, zh)
    """
    
    translated_fields = []
    
    def get_language(self):
        """Get the language from the request query parameters."""
        request = self.context.get('request')
        if request:
            return request.query_params.get('lang', 'en')
        return 'en'
    
    def to_representation(self, instance):
        """Override to substitute translated field values."""
        data = super().to_representation(instance)
        lang = self.get_language()
        
        if lang and lang != 'en' and lang in SUPPORTED_LANGUAGES:
            for field_name in self.translated_fields:
                if field_name in data:
                    translated_attr = f"{field_name}_{lang}"
                    if not hasattr(instance, translated_attr):
                        continue
                    translated_value = getattr(instance, translated_attr, None)
                    if not translated_value:
                        continue
                    # Use the corresponding serializer field to properly render
                    # complex values (e.g. ImageField/FileField -> URL string)
                    field = self.fields.get(field_name) if hasattr(self, 'fields') else None
                    if field is not None:
                        try:
                            data[field_name] = field.to_representation(translated_value)
                        except Exception:
                            data[field_name] = translated_value
                    else:
                        data[field_name] = translated_value
        
        return data
