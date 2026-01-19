from rest_framework import serializers
from .models import ClientReview, PricingPlan, PlanFeature, Contact, ContactInfo, Partner, MainBanner, HowItWorks, HowItWorksStep, TrustSafety, TrustSafetyFeature, SuccessSteps, SuccessStep
from dmv.translation import TranslatedSerializerMixin


class ClientReviewSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for ClientReview model.
    Returns all active client reviews with their details.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['job_title', 'review_text']
    
    class Meta:
        model = ClientReview
        fields = [
            "id",
            "avatar",
            "image",
            "name",
            "job_title",
            "rating",
            "review_text",
            "order",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PlanFeatureSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for PlanFeature model.
    Returns feature details including text, icon, and inclusion status.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['text', 'detail_text']
    icon_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PlanFeature
        fields = [
            "id",
            "text",
            "is_included",
            "icon_type",
            "icon",
            "icon_url",
            "detail_text",
            "order",
        ]
        read_only_fields = ["id"]
    
    def get_icon_url(self, obj):
        """
        Return the icon URL, prioritizing custom uploaded icon over icon_type.
        """
        return obj.get_icon_url()


class PricingPlanSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for PricingPlan model with nested features.
    Returns complete pricing plan information with all features.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['subtitle', 'title', 'description', 'price_period', 'button_text']
    features = serializers.SerializerMethodField()
    
    # Computed fields
    save_text = serializers.SerializerMethodField()
    
    class Meta:
        model = PricingPlan
        fields = [
            "id",
            "subtitle",
            "title",
            "description",
            "price_old",
            "price_period",
            "price_new",
            "discount_amount",
            "save_text",
            "button_text",
            "button_url",
            "is_featured",
            "order",
            "stripe_price_id_monthly",
            "stripe_price_id_one_time",
            "features",
        ]
        read_only_fields = ["id"]
    
    def get_features(self, obj):
        """
        Return features with context for translation support.
        """
        return PlanFeatureSerializer(obj.features.all(), many=True, context=self.context).data
    
    def get_save_text(self, obj):
        """
        Generate save text from discount amount.
        """
        if obj.discount_amount > 0:
            return f"Save ${int(obj.discount_amount)}"
        return ""


class ContactInfoSerializer(serializers.ModelSerializer):
    """
    Serializer for ContactInfo model.
    Returns contact page information (address, phones, emails).
    """
    
    class Meta:
        model = ContactInfo
        fields = [
            "id",
            "address_line1",
            "address_line2",
            "phone_primary",
            "phone_secondary",
            "email_primary",
            "email_secondary",
        ]
        read_only_fields = ["id"]


class ContactSerializer(serializers.ModelSerializer):
    """
    Serializer for Contact model.
    Used for creating contact form submissions.
    """
    
    class Meta:
        model = Contact
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "message",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PartnerSerializer(serializers.ModelSerializer):
    """
    Serializer for Partner model.
    Returns partner information with logo, description, and website URL.
    """
    
    class Meta:
        model = Partner
        fields = [
            "id",
            "logo",
            "description",
            "website_url",
            "order",
        ]
        read_only_fields = ["id"]


class MainBannerSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for MainBanner model.
    Returns main banner content with image, title, description, stats, button, and video.
    The 'link' field returns either video URL or button_link based on use_video_as_button_link.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['title', 'title2', 'description', 'stat_text1', 'stat_text2', 'button_name']
    link = serializers.SerializerMethodField()
    
    class Meta:
        model = MainBanner
        fields = [
            "id",
            "image",
            "title",
            "title2",
            "description",
            "stat_text1",
            "stat_text2",
            "button_name",
            "button_link",
            "video",
            "use_video_as_button_link",
            "link",
        ]
        read_only_fields = ["id"]
    
    def get_link(self, obj):
        """
        Return full video URL if use_video_as_button_link is True, otherwise return button_link.
        """
        if obj.use_video_as_button_link and obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
            return obj.video.url
        return obj.button_link


class HowItWorksStepSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for HowItWorksStep model.
    Returns individual step details with number, title, description, and optional icon.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['title', 'description']
    
    class Meta:
        model = HowItWorksStep
        fields = [
            "id",
            "step_number",
            "title",
            "description",
            "icon",
            "order",
        ]
        read_only_fields = ["id"]


class HowItWorksSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for HowItWorks model with nested steps.
    Returns complete How It Works section with all steps.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['section_header', 'title', 'description']
    steps = serializers.SerializerMethodField()
    
    class Meta:
        model = HowItWorks
        fields = [
            "id",
            "background_image",
            "section_header",
            "title",
            "description",
            "steps",
        ]
        read_only_fields = ["id"]
    
    def get_steps(self, obj):
        """
        Return steps with context for translation support.
        """
        return HowItWorksStepSerializer(obj.steps.all(), many=True, context=self.context).data


class TrustSafetyFeatureSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for TrustSafetyFeature model.
    Returns individual feature details with number, title, and description.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['title', 'description']
    
    class Meta:
        model = TrustSafetyFeature
        fields = [
            "id",
            "number",
            "title",
            "description",
            "order",
        ]
        read_only_fields = ["id"]


class TrustSafetySerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for TrustSafety model with nested features.
    Returns complete Trust & Safety section with all features.
    The 'video_path' field returns the full URL path to the uploaded video file.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['section_header', 'title', 'button_text']
    features = serializers.SerializerMethodField()
    video_path = serializers.SerializerMethodField()
    
    class Meta:
        model = TrustSafety
        fields = [
            "id",
            "section_header",
            "title",
            "image",
            "video",
            "video_path",
            "button_text",
            "button_link",
            "features",
        ]
        read_only_fields = ["id"]
    
    def get_features(self, obj):
        """
        Return features with context for translation support.
        """
        return TrustSafetyFeatureSerializer(obj.features.all(), many=True, context=self.context).data
    
    def get_video_path(self, obj):
        """
        Return full video URL path if video is uploaded.
        """
        if obj.video:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.video.url)
            return obj.video.url
        return None


class SuccessStepSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for SuccessStep model.
    Returns individual step details with icon, title, and description.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['title', 'description']
    
    class Meta:
        model = SuccessStep
        fields = [
            "id",
            "icon",
            "title",
            "description",
            "order",
        ]
        read_only_fields = ["id"]


class SuccessStepsSerializer(TranslatedSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for SuccessSteps model with nested steps.
    Returns complete Success Steps section with all steps.
    Supports translations via ?lang= query parameter.
    """
    translated_fields = ['title', 'description', 'button_text']
    steps = serializers.SerializerMethodField()
    
    class Meta:
        model = SuccessSteps
        fields = [
            "id",
            "title",
            "description",
            "button_text",
            "button_link",
            "steps",
        ]
        read_only_fields = ["id"]
    
    def get_steps(self, obj):
        """
        Return steps with context for translation support.
        """
        return SuccessStepSerializer(obj.steps.all(), many=True, context=self.context).data
