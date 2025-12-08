# Pricing Plans Implementation

## Overview
Complete implementation of the pricing plans feature for the DMV test preparation platform. This implementation replaces the old `Plan` and `Feature` models with new `PricingPlan` and `PlanFeature` models.

## Models

### PricingPlan
Located in `site_details/models.py`

**Fields:**
- **subtitle**: Plan category (e.g., "STATE-SPECIFIC")
- **title**: Plan name (e.g., "7-Day Express", "30-Day All-Access")
- **description**: Brief description of the plan
- **price_old**: Old/original price that will be crossed out (e.g., 49.00)
- **price_period**: Price period text (e.g., "/month")
- **price_new**: New/current price (e.g., 39.00)
- **discount_amount**: Discount amount shown in badge (e.g., 10 for "Save $10")
- **button_text**: CTA button text (default: "Start my plan")
- **button_url**: URL or route for the CTA button
- **is_featured**: Highlight this plan with special styling (border)
- **order**: Display order (lower numbers appear first)
- **is_active**: Whether this plan is visible on the site
- **stripe_price_id_monthly**: Stripe Price ID for monthly subscription
- **stripe_price_id_one_time**: Stripe Price ID for one-time payment
- **created_at**: Timestamp when plan was created
- **updated_at**: Timestamp when plan was last updated

### PlanFeature
Located in `site_details/models.py`

**Fields:**
- **plan**: ForeignKey to PricingPlan (related_name="features")
- **text**: Feature description (e.g., "All 650 exam-like questions for your state")
- **is_included**: Whether this feature is included (unchecked = grayed out)
- **icon_type**: Icon to display next to the feature
  - Choices: check, star, document, car, trophy, lock, unlock
- **order**: Display order within the plan
- **detail_text**: Optional detailed description (shown on hover/click)

## API Endpoints

### GET /api/site-details/pricing-plans/
Retrieve all active pricing plans with their features.

**Response Format:**
```json
{
  "success": true,
  "error": null,
  "data": [
    {
      "id": 1,
      "subtitle": "STATE-SPECIFIC",
      "title": "7-Day Express",
      "description": "Perfect for last-minute test-takers to get you fully ready in less than a week.",
      "price_old": "49.00",
      "price_period": "/month",
      "price_new": "39.00",
      "discount_amount": "10.00",
      "save_text": "Save $10",
      "button_text": "Start my plan",
      "button_url": "/checkout/7-day",
      "is_featured": false,
      "order": 0,
      "stripe_price_id_monthly": "price_xxx",
      "stripe_price_id_one_time": "price_yyy",
      "features": [
        {
          "id": 1,
          "text": "Pass Guarantee (100% money back)",
          "is_included": true,
          "icon_type": "check",
          "detail_text": "",
          "order": 0
        },
        {
          "id": 2,
          "text": "All 650 exam-like questions for your state",
          "is_included": true,
          "icon_type": "check",
          "detail_text": "",
          "order": 1
        }
      ]
    }
  ]
}
```

### GET /api/site-details/reviews/
Retrieve all active client reviews (unchanged).

## Admin Interface

### PricingPlan Admin
Located in `site_details/admin.py`

**Features:**
- List view with columns: title, subtitle, pricing, discount, featured status, order, active status, feature count
- Inline editing for: is_featured, order, is_active
- Filters: is_featured, is_active, created_at
- Search: title, subtitle, description
- Fieldsets organized by:
  - Plan Information
  - Pricing
  - Call to Action
  - Stripe Integration (collapsed)
  - Display Settings
  - Timestamps (collapsed)
- **Inline feature management**: Add/edit features directly within the plan

**Custom Display Methods:**
- `price_display`: Shows both monthly and one-time prices
- `discount_display`: Shows discount amount in green if available
- `feature_count`: Shows number of features in the plan

### PlanFeature Inline
- Tabular inline for managing features
- Fields: text, is_included, icon_type, detail_text, order
- Ordered by display order

## Usage in Admin

### Creating a New Pricing Plan

1. Go to Django Admin → Site Details → Pricing Plans
2. Click "Add Pricing Plan"
3. Fill in the plan information:
   - **Subtitle**: "STATE-SPECIFIC"
   - **Title**: "7-Day Express"
   - **Description**: "Perfect for last-minute test-takers..."
   - **Price old**: 49.00 (will be crossed out)
   - **Price period**: /month
   - **Price new**: 39.00 (current price)
   - **Discount amount**: 10
   - **Button text**: "Start my plan"
   - **Button URL**: "/checkout/7-day"
   - **Is featured**: Check if this is the highlighted plan
   - **Order**: 0 (for first position)
   - **Is active**: Check to make visible

4. Add features inline:
   - **Text**: "Pass Guarantee (100% money back)"
   - **Is included**: Checked
   - **Icon type**: check
   - **Order**: 0

5. Add Stripe Price IDs (optional, for payment integration)

6. Save the plan

### Example: Creating the "30-Day All-Access" Plan

```
Subtitle: STATE-SPECIFIC
Title: 30-Day All-Access
Description: Monthly subscription. Study stress-freewith plenty of time. Cancel online anytime (2 clicks)
Price Old: 99.00 (crossed out)
Price Period: /month
Price New: 88.00 (current price)
Discount Amount: 10.00
Button Text: Start my plan
Button URL: /checkout/30-day
Is Featured: Yes (this will add the blue border)
Order: 1
Is Active: Yes

Features:
1. Pass Guarantee (100% money back) - included, check icon
2. All 650 exam-like questions for your state - included, check icon
3. 14 Behind-the-Wheel Simulators - included, check icon
4. Virtual 360° Road Situations - included, check icon
5. 2 Cheat Sheets (most common questions) - included, document icon
6. 500+ DMV flashcards - included, check icon
7. DMV Genie AI & Challenge Bank™ - included, star icon
8. Unlimited DMV exam simulators - included, unlock icon
9. Priority email and chat support - included, check icon
```

## Migration Notes

- Old `Plan` and `Feature` models have been deleted
- New `PricingPlan` and `PlanFeature` models created
- Migration file: `site_details/migrations/0003_pricingplan_planfeature_delete_feature_delete_plan.py`
- **Important**: Any existing plan data will be lost. You'll need to recreate plans in the admin.

## Files Modified

1. **site_details/models.py**: New PricingPlan and PlanFeature models
2. **site_details/serializers.py**: New serializers for the models
3. **site_details/views.py**: Updated API views with standardized responses
4. **site_details/urls.py**: Updated URL from `/plans/` to `/pricing-plans/`
5. **site_details/admin.py**: Comprehensive admin interface with inline features
6. **dmv/urls.py**: Removed old PricingView import

## Key Improvements

1. **Clear pricing structure**: `price_old` (crossed out) and `price_new` (current) with `price_period` text
2. **Automatic save text**: Computed from `discount_amount` field
3. **Icon choices**: Predefined icon types instead of FontAwesome classes
4. **Detail text**: Optional field for expandable feature descriptions
5. **Stripe integration**: Built-in fields for Stripe Price IDs
6. **Timestamps**: Automatic tracking of creation and update times
7. **Standardized API responses**: Uses the project's APIResponse class
8. **Better admin UX**: Inline feature editing, custom display methods, organized fieldsets

## Next Steps

1. Create pricing plans in the Django admin
2. Add features to each plan
3. Test the API endpoint: `GET /api/site-details/pricing-plans/`
4. Integrate with frontend to display pricing cards
5. Connect with Stripe for payment processing
