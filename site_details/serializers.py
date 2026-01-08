from rest_framework import serializers
from .models import ClientReview, PricingPlan, PlanFeature, Contact, ContactInfo, Partner, MainBanner, HowItWorks, HowItWorksStep


class ClientReviewSerializer(serializers.ModelSerializer):
    """
    Serializer for ClientReview model.
    Returns all active client reviews with their details.
    """
    
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


class PlanFeatureSerializer(serializers.ModelSerializer):
    """
    Serializer for PlanFeature model.
    Returns feature details including text, icon, and inclusion status.
    """
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


class PricingPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for PricingPlan model with nested features.
    Returns complete pricing plan information with all features.
    """
    features = PlanFeatureSerializer(many=True, read_only=True)
    
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
    Returns partner information with logo and description.
    """
    
    class Meta:
        model = Partner
        fields = [
            "id",
            "logo",
            "description",
            "order",
        ]
        read_only_fields = ["id"]


class MainBannerSerializer(serializers.ModelSerializer):
    """
    Serializer for MainBanner model.
    Returns main banner content with image, title, and description.
    """
    
    class Meta:
        model = MainBanner
        fields = [
            "id",
            "image",
            "title",
            "title2",
            "description",
        ]
        read_only_fields = ["id"]


class HowItWorksStepSerializer(serializers.ModelSerializer):
    """
    Serializer for HowItWorksStep model.
    Returns individual step details with number, title, description, and optional icon.
    """
    
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


class HowItWorksSerializer(serializers.ModelSerializer):
    """
    Serializer for HowItWorks model with nested steps.
    Returns complete How It Works section with all steps.
    """
    steps = HowItWorksStepSerializer(many=True, read_only=True)
    
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
