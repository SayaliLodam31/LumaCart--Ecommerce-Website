import os
from PIL import Image, ImageDraw, ImageFont

# Dimensions
size = 512
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Colors from LumaCart theme
# Base: #FAF9F6 (Warm Ivory)
# Border: #E8E4DC (Muted sand)
# Text: #1F1F1F (Deep charcoal)
# Dot: #8A9A86 (Muted Sage)
bg_color = (250, 249, 246, 255)
border_color = (232, 228, 220, 255)
text_color = (31, 31, 31, 255)
dot_color = (138, 154, 134, 255)

# Rounded rectangle container (squircle fashion badge)
margin = 24
radius = 110
draw.rounded_rectangle(
    [margin, margin, size - margin, size - margin],
    radius=radius,
    fill=bg_color,
    outline=border_color,
    width=14
)

# Render Serif Letter 'L'
font_path = "C:/Windows/Fonts/georgiab.ttf"
font_size = 310
font = ImageFont.truetype(font_path, font_size)

# Calculate bounding box to position precisely in center-left
# 'L'
bbox = draw.textbbox((0, 0), "L", font=font)
text_w = bbox[2] - bbox[0]
text_h = bbox[3] - bbox[1]

# Position L slightly left of center to allow room for the signature sage brand dot
offset_x = (size - text_w) // 2 - 25
offset_y = (size - text_h) // 2 - 35 - bbox[1]

draw.text((offset_x, offset_y), "L", fill=text_color, font=font)

# Signature sage green brand dot (matching LumaCart .logo-dot)
# Place at upper right of the horizontal foot of L, or upper right of monogram
dot_radius = 28
dot_cx = offset_x + text_w + 32
dot_cy = offset_y + bbox[3] - 40

draw.ellipse(
    [dot_cx - dot_radius, dot_cy - dot_radius, dot_cx + dot_radius, dot_cy + dot_radius],
    fill=dot_color
)

# Output directories
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend'))
assets_img_dir = os.path.join(frontend_dir, 'assets', 'images')
os.makedirs(assets_img_dir, exist_ok=True)

# 1. High-res Apple Touch Icon (180x180)
apple_icon = img.resize((180, 180), Image.Resampling.LANCZOS)
apple_icon.save(os.path.join(assets_img_dir, 'apple-touch-icon.png'), 'PNG')

# 2. 32x32 PNG
icon_32 = img.resize((32, 32), Image.Resampling.LANCZOS)
icon_32.save(os.path.join(assets_img_dir, 'favicon-32x32.png'), 'PNG')

# 3. 16x16 PNG
icon_16 = img.resize((16, 16), Image.Resampling.LANCZOS)
icon_16.save(os.path.join(assets_img_dir, 'favicon-16x16.png'), 'PNG')

# 4. Multi-resolution ICO (16, 32, 48)
ico_img = img.resize((48, 48), Image.Resampling.LANCZOS)
ico_path_assets = os.path.join(assets_img_dir, 'favicon.ico')
ico_path_root = os.path.join(frontend_dir, 'favicon.ico')

ico_img.save(
    ico_path_assets,
    format='ICO',
    sizes=[(16, 16), (32, 32), (48, 48)]
)
ico_img.save(
    ico_path_root,
    format='ICO',
    sizes=[(16, 16), (32, 32), (48, 48)]
)

print('Generated PNG and ICO favicons successfully!')
