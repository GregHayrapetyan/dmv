# Pricing Plans - Example Data

This document provides the exact data to enter in the Django admin to recreate the pricing plans from the design.

## Plan 1: 7-Day Express (Left Card)

### Plan Details
```
Subtitle: STATE-SPECIFIC
Title: 7-Day Express
Description: Perfect for last-minute test-takers to get you fully ready in less than a week.
Price Old: 49.00 (this will be crossed out)
Price Period: /month
Price New: 39.00 (this is the current price)
Discount Amount: 10.00
Button Text: Start my plan
Button URL: /checkout/7-day-express
Is Featured: No
Order: 0
Is Active: Yes
```

### Features (in order)
1. **Pass Guarantee (100% money back)**
   - Is included: ✓
   - Icon type: check
   - Order: 0

2. **All 650 exam-like questions for your state**
   - Is included: ✓
   - Icon type: check
   - Order: 1

3. **14 Behind-the-Wheel Simulators**
   - Is included: ✓
   - Icon type: check
   - Order: 2

4. **Virtual 360° Road Situations**
   - Is included: ✓
   - Icon type: check
   - Order: 3

5. **2 Cheat Sheets (most common questions)**
   - Is included: ✓
   - Icon type: document
   - Order: 4

6. **500+ DMV flashcards**
   - Is included: ✓
   - Icon type: check
   - Order: 5

7. **DMV Genie AI & Challenge Bank™**
   - Is included: ✗ (grayed out)
   - Icon type: lock
   - Order: 6

8. **Unlimited DMV exam simulators**
   - Is included: ✗ (grayed out)
   - Icon type: lock
   - Order: 7

9. **Priority email and chat support**
   - Is included: ✗ (grayed out)
   - Icon type: lock
   - Order: 8

---

## Plan 2: 30-Day All-Access (Center Card - Featured)

### Plan Details
```
Subtitle: STATE-SPECIFIC
Title: 30-Day All-Access
Description: Monthly subscription. Study stress-freewith plenty of time. Cancel online anytime (2 clicks)
Price Old: 99.00 (this will be crossed out)
Price Period: /month
Price New: 88.00 (this is the current price)
Discount Amount: 10.00
Button Text: Start my plan
Button URL: /checkout/30-day-all-access
Is Featured: Yes (This adds the blue border!)
Order: 1
Is Active: Yes
```

### Features (in order)
1. **Pass Guarantee (100% money back)**
   - Is included: ✓
   - Icon type: check
   - Order: 0

2. **All 650 exam-like questions for your state**
   - Is included: ✓
   - Icon type: check
   - Order: 1

3. **14 Behind-the-Wheel Simulators**
   - Is included: ✓
   - Icon type: check
   - Order: 2

4. **Virtual 360° Road Situations**
   - Is included: ✓
   - Icon type: check
   - Order: 3

5. **2 Cheat Sheets (most common questions)**
   - Is included: ✓
   - Icon type: document
   - Order: 4

6. **500+ DMV flashcards**
   - Is included: ✓
   - Icon type: check
   - Order: 5

7. **DMV Genie AI & Challenge Bank™**
   - Is included: ✓
   - Icon type: star
   - Order: 6

8. **Unlimited DMV exam simulators**
   - Is included: ✓
   - Icon type: unlock
   - Order: 7

9. **Priority email and chat support**
   - Is included: ✓
   - Icon type: check
   - Order: 8

---

## Plan 3: 7-Day Express (Right Card - Duplicate)

### Plan Details
```
Subtitle: STATE-SPECIFIC
Title: 7-Day Express
Description: Perfect for last-minute test-takers to get you fully ready in less than a week.
Price Old: 49.00 (this will be crossed out)
Price Period: /month
Price New: 39.00 (this is the current price)
Discount Amount: 10.00
Button Text: Start my plan
Button URL: /checkout/7-day-express-2
Is Featured: No
Order: 2
Is Active: Yes
```

### Features (in order)
Same as Plan 1 (7-Day Express)

---

## Quick Admin Entry Guide

1. **Login to Django Admin**: `/admin/`
2. **Navigate to**: Site Details → Pricing Plans
3. **Click**: "Add Pricing Plan"
4. **Fill in the form** with the plan details above
5. **Scroll down to "Plan features"** section
6. **Click "Add another Plan feature"** for each feature
7. **Enter feature details** as listed above
8. **Save** the plan

## Icon Type Reference

When entering features, use these icon types:
- `check` - Checkmark (✓) for included features
- `lock` - Lock (🔒) for locked/unavailable features
- `unlock` - Unlock (🔓) for unlocked premium features
- `star` - Star (⭐) for special/premium features
- `document` - Document (📄) for downloadable content
- `car` - Car (🚗) for driving-related features
- `trophy` - Trophy (🏆) for achievements

## Testing the API

After creating the plans, test the API endpoint:

```bash
curl http://localhost:8000/api/site-details/pricing-plans/
```

Expected response structure:
```json
{
  "success": true,
  "error": null,
  "data": [
    {
      "id": 1,
      "subtitle": "STATE-SPECIFIC",
      "title": "7-Day Express",
      "price_monthly": "49.00",
      "price_one_time": "39.00",
      "save_text": "Save $10",
      "is_featured": false,
      "features": [...]
    },
    ...
  ]
}
```

## Notes

- The **Is Featured** checkbox adds special styling (blue border) to highlight the recommended plan
- **Order** determines left-to-right display (0 = leftmost)
- **Is included** checkbox controls whether a feature is grayed out or active
- **Detail text** is optional and can be used for tooltips/expandable descriptions
- Stripe Price IDs can be added later when setting up payment processing
