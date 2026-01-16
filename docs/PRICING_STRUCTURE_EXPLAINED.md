# Pricing Structure Explained

## Understanding the Pricing Display

Based on your pricing card image, here's how the pricing works:

### Visual Breakdown

```
┌─────────────────────────────────────┐
│  STATE-SPECIFIC                     │ ← subtitle
│  7-Day Express                      │ ← title
│                                     │
│  $49 /month  $39                    │ ← price_old + price_period + price_new
│   ↑           ↑                     │
│  crossed out  current price         │
│                                     │
│  [Save $10]                         │ ← discount_amount (auto-generated badge)
│                                     │
│  [Start my plan]                    │ ← button_text
└─────────────────────────────────────┘
```

## Model Fields Mapping

### PricingPlan Model

| Field | Example Value | Display | Purpose |
|-------|---------------|---------|---------|
| `price_old` | 49.00 | ~~$49~~ | Original price (crossed out) |
| `price_period` | "/month" | /month | Period text next to old price |
| `price_new` | 39.00 | **$39** | Current/sale price (bold) |
| `discount_amount` | 10.00 | Save $10 | Auto-generates green badge |

## Frontend Display Logic

When rendering the pricing card on the frontend:

```javascript
// Example React/JavaScript rendering
<div className="pricing-card">
  <div className="price-section">
    {plan.price_old && (
      <span className="price-old">
        ${plan.price_old} {plan.price_period}
      </span>
    )}
    <span className="price-new">
      ${plan.price_new}
    </span>
  </div>
  
  {plan.discount_amount > 0 && (
    <div className="discount-badge">
      {plan.save_text}
    </div>
  )}
</div>
```

### CSS Styling

```css
.price-old {
  text-decoration: line-through;
  color: #999;
  font-size: 14px;
}

.price-new {
  font-size: 32px;
  font-weight: bold;
  color: #000;
}

.discount-badge {
  background: #4caf50;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
}
```

## Admin Interface

When you create a plan in Django Admin, you'll see:

### Pricing Section
```
┌─────────────────────────────────────────────┐
│ PRICING                                     │
│ Price old is crossed out (e.g., $49 /month).│
│ Price new is the current price (e.g., $39). │
│                                             │
│ Price old: [49.00]  Price period: [/month] │
│ Price new: [39.00]                          │
│ Discount amount: [10.00]                    │
└─────────────────────────────────────────────┘
```

### List View Display
In the admin list view, you'll see pricing displayed as:
```
~~$49~~ /month → $39
```

## API Response

The API endpoint `/api/site-details/pricing-plans/` returns:

```json
{
  "success": true,
  "error": null,
  "data": [
    {
      "id": 1,
      "subtitle": "STATE-SPECIFIC",
      "title": "7-Day Express",
      "price_old": "49.00",
      "price_period": "/month",
      "price_new": "39.00",
      "discount_amount": "10.00",
      "save_text": "Save $10",
      "button_text": "Start my plan",
      "is_featured": false,
      "features": [...]
    }
  ]
}
```

## Real Examples from Your Design

### 7-Day Express Plan
- **price_old**: 49.00
- **price_period**: /month
- **price_new**: 39.00
- **discount_amount**: 10.00
- **Result**: Shows "~~$49~~ /month **$39**" with "Save $10" badge

### 30-Day All-Access Plan
- **price_old**: 99.00
- **price_period**: /month
- **price_new**: 88.00
- **discount_amount**: 10.00
- **Result**: Shows "~~$99~~ /month **$88**" with "Save $10" badge

## Important Notes

1. **price_old is optional**: If you don't set it, only the new price will show
2. **price_period default**: Automatically set to "/month" but can be changed
3. **save_text is computed**: Automatically generated from discount_amount
4. **Admin preview**: Shows crossed-out old price → new price in green

## Migration Applied

The following migration was applied:
- **File**: `site_details/migrations/0004_remove_pricingplan_price_monthly_and_more.py`
- **Changes**:
  - Removed: `price_monthly`, `price_one_time`
  - Added: `price_old`, `price_period`, `price_new`
  - Updated: `discount_amount` help text

## Testing

To test the pricing display:

1. Create a plan in admin with:
   - price_old: 49.00
   - price_period: /month
   - price_new: 39.00
   - discount_amount: 10.00

2. Check the API response:
   ```bash
   curl http://localhost:8000/api/site-details/pricing-plans/
   ```

3. Verify the response includes all pricing fields correctly
