from PIL import Image, ImageDraw, ImageFont
import os

# Create a blank image with a transparent background
size = (256, 256)
image = Image.new('RGBA', size, color=(0, 0, 0, 0))
draw = ImageDraw.Draw(image)

# Draw a rounded rectangle for the background
background_color = (45, 45, 48, 240)  # Dark background with transparency
draw.rounded_rectangle([(20, 20), (236, 236)], radius=30, fill=background_color)

# Draw a maple leaf shape (simplified)
leaf_color = (220, 20, 60, 240)  # Crimson red
# Main body of the leaf
points = [
    (128, 40),  # Top point
    (170, 70),  # Right upper
    (190, 110), # Right middle
    (170, 150), # Right lower
    (128, 180), # Bottom point
    (86, 150),  # Left lower
    (66, 110),  # Left middle
    (86, 70)    # Left upper
]
draw.polygon(points, fill=leaf_color)

# Draw a price tag/shop symbol
tag_color = (255, 215, 0, 240)  # Gold color
draw.rounded_rectangle([(90, 130), (170, 200)], radius=10, fill=tag_color)
draw.polygon([(90, 145), (70, 160), (90, 175)], fill=tag_color)  # Tag extension

# Draw a dollar sign
try:
    # Try to load a font
    font = ImageFont.truetype("arial.ttf", 50)
    draw.text((115, 140), "$", fill=(0, 0, 0, 240), font=font)
except:
    # Fallback if font not available
    draw.text((115, 140), "$", fill=(0, 0, 0, 240))

# Save as PNG
image.save('app_icon.png')

# Convert to ICO
image.save('app.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])

print("New icon created successfully!")
