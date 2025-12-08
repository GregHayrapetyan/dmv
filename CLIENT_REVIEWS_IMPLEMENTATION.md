# Client Reviews Implementation

## Overview
Created a complete client review system in the `site_details` app with model, API endpoints, and admin panel integration.

## What Was Created

### 1. Model: `ClientReview`
**Location:** `/home/greg/dmv/site_details/models.py`

**Fields:**
- `avatar` - ImageField for client profile picture (uploaded to `reviews/avatars/`)
- `name` - CharField for client name (e.g., "Bimosaurus")
- `job_title` - CharField for client job title (e.g., "Graphic Designer")
- `rating` - PositiveSmallIntegerField (1-5 stars)
- `review_text` - TextField for the testimonial text
- `order` - PositiveIntegerField for display ordering
- `is_active` - BooleanField to show/hide reviews
- `created_at` - DateTimeField (auto-generated)
- `updated_at` - DateTimeField (auto-updated)

### 2. Admin Panel Integration
**Location:** `/home/greg/dmv/site_details/admin.py`

**Features:**
- List view with name, job title, rating (as stars ⭐), avatar preview, order, status, and date
- Inline editing for order and is_active fields
- Filters by rating, active status, and creation date
- Search by name, job title, and review text
- Avatar preview thumbnail (50px circular)
- Rating displayed as star emojis
- Organized fieldsets for better UX
- Readonly timestamps

### 3. API Endpoints
**Location:** `/home/greg/dmv/site_details/views.py` and `/home/greg/dmv/site_details/urls.py`

**Endpoints:**
- `GET /api/site-details/reviews/` - List all active client reviews
- `GET /api/site-details/plans/` - List all active pricing plans (bonus)

**Response Format (Reviews):**
```json
[
  {
    "id": 1,
    "avatar": "/media/reviews/avatars/client1.jpg",
    "name": "Bimosaurus",
    "job_title": "Graphic Designer",
    "rating": 5,
    "review_text": "I've used other kits, but this one is the best...",
    "order": 0,
    "created_at": "2024-12-08T17:58:00Z"
  }
]
```

### 4. Serializers
**Location:** `/home/greg/dmv/site_details/serializers.py`

Created serializers for:
- `ClientReviewSerializer` - For review data
- `PlanSerializer` - For pricing plans with nested features
- `FeatureSerializer` - For plan features

## How to Use

### Adding Reviews via Admin Panel
1. Navigate to Django admin: `/admin/`
2. Go to "Site Details" → "Client Reviews"
3. Click "Add Client Review"
4. Fill in all fields:
   - Upload avatar image
   - Enter client name
   - Enter job title
   - Select rating (1-5 stars)
   - Write review text
   - Set display order (lower = appears first)
   - Check "is active" to display on site
5. Save

### Accessing via API
```bash
# Get all active reviews
curl http://localhost:8000/api/site-details/reviews/

# Get all active pricing plans
curl http://localhost:8000/api/site-details/plans/
```

## Migration
A migration file was created: `site_details/migrations/0002_clientreview.py`

**To apply the migration, run:**
```bash
python manage.py migrate
```

## Notes
- Images are stored in `media/reviews/avatars/`
- Only active reviews (`is_active=True`) are returned by the API
- Reviews are ordered by `order` field, then by creation date (newest first)
- All API endpoints are publicly accessible (AllowAny permission)
- Avatar preview in admin shows 50px circular thumbnail
- Rating is displayed as star emojis in admin list view
