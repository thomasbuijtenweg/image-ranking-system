# Image Ranking System - Tier-Based UI Color Changes

## Summary
Modified the IRS to display a red/warning color scheme when comparing images in tier -2 and lower, making it visually clear when viewing potential binning candidates.

## Files Modified

### 1. config.py
**Added new color constants for binning tier warnings:**
- `BG_BINNING_PRIMARY = '#3d1e1e'` - Dark red background
- `BG_BINNING_SECONDARY = '#4d2d2d'` - Slightly lighter dark red
- `BG_BINNING_TERTIARY = '#5d3d3d'` - Even lighter red for image area
- `BORDER_BINNING = '#ff4444'` - Red border

### 2. ui/components/image_display.py
**Added tier-based color functionality:**

1. **New method `_get_tier_colors(tier)`:**
   - Returns appropriate color scheme based on tier level
   - Tier -2 and lower: Red warning colors
   - All other tiers: Normal dark theme colors

2. **New method `_update_frame_colors(side, tier)`:**
   - Updates all frame elements (background, image area, info labels) with tier-appropriate colors
   - Applies colors to the specified side (left or right)

3. **Modified `display_image(filename, side)`:**
   - Now retrieves the image's tier from stats
   - Calls `_update_frame_colors()` before displaying the image
   - Color scheme updates automatically when new images are shown

4. **Modified `update_image_info(filename, side)`:**
   - Added "⚠️ BINNING CANDIDATE" indicator to tier display when tier <= -2
   - Makes it clear in the info text that the image is a binning candidate

5. **Modified `clear_images()`:**
   - Resets frame colors to normal (tier 0) when clearing images

## How It Works

### Visual Feedback
When comparing images:
- **Normal tiers (≥ -1)**: Standard dark gray theme
- **Binning tiers (≤ -2)**: Red-tinted theme with warning indicator

### Color Application
The system checks the tier of each image when displaying:
```python
tier = stats.get('current_tier', 0)
self._update_frame_colors(side, tier)
```

### User Experience
1. User navigates through image comparisons normally
2. When either or both images are in tier -2 or lower:
   - The frame background turns dark red
   - The image display area has a red tint
   - Info and metadata labels have matching red background
   - A "⚠️ BINNING CANDIDATE" warning appears in the tier info
3. This provides immediate visual feedback that these images should be considered for binning

## Benefits
- **Clear visual distinction** between normal images and potential binning candidates
- **Non-intrusive** - uses existing UI elements with color changes
- **Automatic** - no user action needed, works seamlessly during normal ranking
- **Consistent** - applies to any image in tier -2 or lower, regardless of how they got there

## Testing Recommendations
1. Load a set of images with mixed tier levels
2. Vote until some images reach tier -2 or lower
3. Verify that frames turn red when displaying low-tier images
4. Confirm that the warning indicator appears in the tier info
5. Check that colors reset properly when clearing images or loading new sets
