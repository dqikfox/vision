"""Analyze the avatar's visible colors"""
import numpy as np
from PIL import Image

# Load the extracted canvas
img = Image.open('canvas_direct.png')
img_array = np.array(img)

print(f"Image size: {img.size}")
print(f"Image mode: {img.mode}")

if len(img_array.shape) == 3:
    if img_array.shape[2] == 4:  # RGBA
        # Separate RGB and alpha
        rgb = img_array[:, :, :3]
        alpha = img_array[:, :, 3]

        # Find visible pixels (alpha > 10 and not pure black)
        visible_mask = (alpha > 10) & (np.sum(rgb, axis=2) > 30)
        visible_pixels = rgb[visible_mask]

        if len(visible_pixels) > 0:
            print(f"\nVisible pixels: {len(visible_pixels):,}")

            # Analyze color distribution
            avg_color = np.mean(visible_pixels, axis=0)
            print(f"Average RGB color: ({avg_color[0]:.1f}, {avg_color[1]:.1f}, {avg_color[2]:.1f})")
            print(f"Average as hex: #{int(avg_color[0]):02x}{int(avg_color[1]):02x}{int(avg_color[2]):02x}")

            # Find brightest pixel
            brightness = np.sum(visible_pixels, axis=1)
            brightest_idx = np.argmax(brightness)
            brightest = visible_pixels[brightest_idx]
            print(f"\nBrightest pixel: RGB({brightest[0]}, {brightest[1]}, {brightest[2]})")
            print(f"Brightest as hex: #{brightest[0]:02x}{brightest[1]:02x}{brightest[2]:02x}")

            # Count pixels by color range
            # Blues/Purples (Ultron colors)
            is_blue = (visible_pixels[:, 2] > visible_pixels[:, 0]) & (visible_pixels[:, 2] > visible_pixels[:, 1])
            is_purple = (visible_pixels[:, 2] > 100) & (visible_pixels[:, 0] > 50)
            is_cyan = (visible_pixels[:, 1] > 100) & (visible_pixels[:, 2] > 100)

            print("\nColor breakdown:")
            print(f"  Blue-tinted pixels: {np.sum(is_blue):,} ({np.sum(is_blue)/len(visible_pixels)*100:.1f}%)")
            print(f"  Purple-tinted pixels: {np.sum(is_purple):,} ({np.sum(is_purple)/len(visible_pixels)*100:.1f}%)")
            print(f"  Cyan-tinted pixels: {np.sum(is_cyan):,} ({np.sum(is_cyan)/len(visible_pixels)*100:.1f}%)")

            # Sample some pixels
            sample_size = min(20, len(visible_pixels))
            sample_indices = np.random.choice(len(visible_pixels), sample_size, replace=False)
            print(f"\nSample of {sample_size} visible pixels:")
            for i, idx in enumerate(sample_indices[:10]):
                px = visible_pixels[idx]
                print(f"  {i+1}. RGB({px[0]:3d}, {px[1]:3d}, {px[2]:3d}) = #{px[0]:02x}{px[1]:02x}{px[2]:02x}")
        else:
            print("\nNo visible pixels found!")
    else:
        print("RGB image (no alpha channel)")
else:
    print("Unexpected image format")
