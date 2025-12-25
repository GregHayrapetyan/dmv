# Pricing Plan Feature Icons

This directory contains SVG icons used for pricing plan features.

## Default Icons

- **check.svg** - Checkmark icon for standard features
- **book.svg** - Book icon for learning/educational features
- **shield.svg** - Shield icon for security/protection features
- **simulation.svg** - Monitor/screen icon for simulation/practice features

## Usage in CMS

When creating or editing a Plan Feature in the Wagtail CMS:

1. **Using Default Icons**: Select one of the predefined icons from the "Icon type" dropdown
2. **Using Custom Icons**: Upload your own SVG file in the "Icon" field (this will override the icon type)

## Custom Icon Guidelines

When uploading custom SVG icons:

- **Format**: SVG only
- **Size**: 24x24 viewBox recommended
- **Style**: Use `stroke="currentColor"` to allow color customization
- **Optimization**: Minimize SVG code for better performance

## API Response

The API will return:
- `icon_type`: The selected default icon path
- `icon`: The custom uploaded icon URL (if provided)
- `icon_url`: The final icon URL to use (custom icon takes priority)

Frontend should use `icon_url` to display the icon.
