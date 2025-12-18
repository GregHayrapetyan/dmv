# Partners Feature Implementation

## Overview
Added a Partners feature to display partner/sponsor logos and information on the website. This includes a database model, admin interface, and public API endpoint.

## What Was Added

### 1. Partner Model (`site_details/models.py`)
- **Fields:**
  - `logo`: ImageField for partner logo (uploaded to `partners/logos/`)
  - `description`: TextField for partner description
  - `order`: PositiveIntegerField for display ordering
  - `is_active`: BooleanField to control visibility
  - `created_at`, `updated_at`: Automatic timestamps

- **Ordering:** By `order` field (ascending), then by `created_at` (descending)
- **Note:** Partner name is not stored separately - the logo image itself represents the partner

### 2. Admin Interface (`site_details/admin.py`)
- **PartnerAdmin** registered at `/admin/site_details/partner/`
- **List Display:**
  - Partner name
  - Logo preview (thumbnail)
  - Description preview (truncated)
  - Order
  - Active status
  - Created date

- **Features:**
  - Inline editing of `order` and `is_active` fields
  - Logo preview in both list and detail views
  - Search by name and description
  - Filter by active status and creation date
  - Organized fieldsets for easy data entry

### 3. API Endpoint

#### GET `/api/site-details/partners/`
- **Description:** Retrieve all active partners
- **Authentication:** None required (public endpoint)
- **Pagination:** Disabled (returns all active partners)
- **Response Format:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "logo": "/media/partners/logos/inecobank.png",
      "name": "INECOBANK",
      "description": "Great potential for cooperation with Ineco Bank for over 10 years",
      "order": 1
    },
    {
      "id": 2,
      "logo": "/media/partners/logos/hsbc.png",
      "name": "HSBC",
      "description": "Great potential for cooperation with Ineco Bank for over 10 years",
      "order": 2
    }
  ]
}
```

### 4. Serializer (`site_details/serializers.py`)
- **PartnerSerializer:** Serializes partner data for API responses
- **Fields:** id, logo, name, description, order
- **Read-only:** id field

### 5. Database Migration
- Migration file: `site_details/migrations/0010_partner.py`
- Creates the `Partner` table with all required fields and indexes

## Usage

### Adding Partners via Admin
1. Navigate to `/admin/site_details/partner/`
2. Click "Add Partner"
3. Fill in:
   - Name (e.g., "INECOBANK")
   - Upload logo image
   - Description (e.g., "Great potential for cooperation...")
   - Order (lower numbers appear first)
   - Check "Is active" to display on site
4. Save

### Fetching Partners via API
```bash
# Get all active partners
curl http://localhost:8000/api/site-details/partners/
```

### Frontend Integration Example
```javascript
// Fetch partners
const response = await fetch('/api/site-details/partners/');
const result = await response.json();

if (result.success) {
  const partners = result.data;
  // Display partners in a grid
  partners.forEach(partner => {
    console.log(partner.name, partner.logo, partner.description);
  });
}
```

## Files Modified
1. `/home/greg/dmv/site_details/models.py` - Added Partner model
2. `/home/greg/dmv/site_details/admin.py` - Added PartnerAdmin
3. `/home/greg/dmv/site_details/serializers.py` - Added PartnerSerializer
4. `/home/greg/dmv/site_details/views.py` - Added PartnerListAPIView
5. `/home/greg/dmv/site_details/urls.py` - Added partners/ route
6. `/home/greg/dmv/site_details/migrations/0010_partner.py` - Database migration

## API Documentation
The endpoint is automatically documented in the OpenAPI schema:
- Swagger UI: `/api/schema/swagger-ui/`
- ReDoc: `/api/schema/redoc/`
- OpenAPI JSON: `/api/schema/`

## Notes
- Partners are ordered by the `order` field (ascending)
- Only active partners (`is_active=True`) are returned by the API
- Logo images are stored in `media/partners/logos/`
- The API uses the standardized `APIResponse` format consistent with other endpoints
- No pagination is applied to keep all partners visible at once
