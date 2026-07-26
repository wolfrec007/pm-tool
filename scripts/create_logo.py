"""Create splanly logo PNG from code."""
from PIL import Image, ImageDraw
import os

# Create a 400x400 image with the splanly logo
size = 400
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background - dark blue rounded rectangle
bg_color = (20, 48, 77)  # #14304d
draw.rounded_rectangle([0, 0, size-1, size-1], radius=80, fill=bg_color)

# Left circle - blue
blue_color = (79, 130, 176, 217)  # #4f82b0 with 0.85 opacity
draw.ellipse([64, 128, 240, 304], fill=blue_color)

# Right circle - white/light
white_color = (238, 245, 252)  # #eef5fc
draw.ellipse([160, 96, 336, 272], fill=white_color)

# Save as PNG
output_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'app', 'static', 'logo.png')
img.save(output_path, 'PNG')
print(f'PNG logo saved to: {output_path}')
print(f'Size: {os.path.getsize(output_path)} bytes')
