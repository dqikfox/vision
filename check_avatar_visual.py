"""Check if avatar is visually present in the screenshot"""
import numpy as np
from PIL import Image

# Load the screenshot
img = Image.open('ui_runtime_state.png')
img_array = np.array(img)

print(f"Image size: {img.size}")
print(f"Image mode: {img.mode}")

# Find the hero area (top-left quadrant approximately)
height, width = img_array.shape[:2]
hero_top = int(height * 0.15)
hero_bottom = int(height * 0.65)
hero_left = int(width * 0.05)
hero_right = int(width * 0.45)

hero_region = img_array[hero_top:hero_bottom, hero_left:hero_right]

# Check if the hero region has significant non-background content
# Background is typically very dark (close to #030611)
if len(hero_region.shape) == 3:
    # RGB image
    # Dark background would be close to (3, 6, 17) in RGB
    # Avatar should have brighter pixels (blues, cyans, etc.)
    avg_brightness = np.mean(hero_region)
    max_brightness = np.max(hero_region)

    # Count pixels brighter than background
    threshold = 50  # Anything brighter than dark background
    bright_pixels = np.sum(hero_region > threshold)
    total_pixels = hero_region.size
    bright_ratio = bright_pixels / total_pixels

    print(f"\nHero region analysis ({hero_right-hero_left}x{hero_bottom-hero_top} pixels):")
    print(f"  Average brightness: {avg_brightness:.1f}")
    print(f"  Max brightness: {max_brightness}")
    print(f"  Bright pixel ratio: {bright_ratio:.2%}")
    print(f"  Bright pixel count: {bright_pixels:,} / {total_pixels:,}")

    if bright_ratio > 0.05:  # More than 5% bright pixels
        print("\n✓ Avatar appears to be VISIBLE (significant bright content detected)")
    else:
        print("\n✗ Avatar may NOT be visible (mostly dark/background)")

    # Save the hero region for inspection
    hero_img = Image.fromarray(hero_region)
    hero_img.save('hero_region.png')
    print("\nHero region saved to: hero_region.png")
else:
    print("Grayscale image detected")
