import os
import aiohttp
from PIL import (
    Image, ImageDraw, ImageEnhance,
    ImageFilter, ImageFont, ImageOps
)

from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        # Canvas Size
        self.width = 1280
        self.height = 720
        self.size = (self.width, self.height)

        # Fonts (Sizes ko adjust kiya hai better look ke liye)
        # Title ke liye bada font
        self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 45)
        # Artist/Channel ke liye medium
        self.font_sub = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 30)
        # Duration/Time ke liye small
        self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 25)

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    with open(output_path, "wb") as f:
                        f.write(await resp.read())
        return output_path

    def truncate_text(self, draw, text, font, max_width):
        """Text ko ... ke saath cut karne ke liye agar wo jyada lamba ho"""
        w = draw.textlength(text, font=font)
        if w > max_width:
            while draw.textlength(text + "...", font=font) > max_width:
                text = text[:-1]
            return text + "..."
        return text

    def add_corners(self, im, rad):
        circle = Image.new('L', (rad * 2, rad * 2), 0)
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, rad * 2, rad * 2), fill=255)
        alpha = Image.new('L', im.size, 255)
        w, h = im.size
        alpha.paste(circle.crop((0, 0, rad, rad)), (0, 0))
        alpha.paste(circle.crop((0, rad, rad, rad * 2)), (0, h - rad))
        alpha.paste(circle.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
        alpha.paste(circle.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))
        im.putalpha(alpha)
        return im

    async def generate(self, song: Track) -> str:
        try:
            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"

            if os.path.exists(output):
                return output

            # 1. Download Image
            await self.save_thumb(temp, song.thumbnail)

            # 2. Prepare Background (Dark & Blurred)
            base_img = Image.open(temp).convert("RGBA").resize(self.size, Image.Resampling.LANCZOS)
            
            # Heavy Blur
            blur = base_img.filter(ImageFilter.GaussianBlur(30))
            # Darken Background (0.3 factor)
            background = ImageEnhance.Brightness(blur).enhance(0.4)
            
            # Vignette/Gradient Overlay (Niche se dark hona chahiye text ke liye)
            overlay = Image.new("RGBA", self.size, (0, 0, 0, 0))
            draw_overlay = ImageDraw.Draw(overlay)
            # Black gradient from bottom
            for y in range(int(self.height / 2), self.height):
                alpha = int(255 * (y - self.height / 2) / (self.height / 2))
                draw_overlay.line([(0, y), (self.width, y)], fill=(0, 0, 0, alpha))
            
            background = Image.alpha_composite(background, overlay)

            # 3. Create Central Album Art (Square with Shadow)
            art_size = 420
            art = Image.open(temp).convert("RGBA")
            art = ImageOps.fit(art, (art_size, art_size), method=Image.Resampling.LANCZOS)
            art = self.add_corners(art, 40) # Rounded corners

            # Create Shadow Effect
            shadow_offset = 20
            shadow = Image.new("RGBA", (art_size + shadow_offset, art_size + shadow_offset), (0,0,0,0))
            shadow_draw = ImageDraw.Draw(shadow)
            # Black rounded box behind
            shadow_draw.rounded_rectangle((shadow_offset, shadow_offset, art_size, art_size), radius=40, fill=(0,0,0, 180))
            shadow = shadow.filter(ImageFilter.GaussianBlur(15)) # Soft shadow

            # Paste Shadow then Art
            center_x = (self.width - art_size) // 2
            center_y = 80 # Top margin
            
            # Shadow paste coordinate needs adjustment
            background.paste(shadow, (center_x - 10, center_y - 10), shadow)
            background.paste(art, (center_x, center_y), art)

            draw = ImageDraw.Draw(background)

            # 4. Text Logic (Centered Design)
            
            # Title
            title_text = self.truncate_text(draw, song.title, self.font_title, 1100)
            title_w = draw.textlength(title_text, font=self.font_title)
            draw.text(
                ((self.width - title_w) / 2, 540),
                title_text,
                font=self.font_title,
                fill=(255, 255, 255)
            )

            # Channel / Artist
            channel_text = f"{song.channel_name}  |  Views: {song.view_count}"
            chan_w = draw.textlength(channel_text, font=self.font_sub)
            draw.text(
                ((self.width - chan_w) / 2, 595),
                channel_text,
                font=self.font_sub,
                fill=(200, 200, 200) # Light Gray
            )

            # 5. Modern Progress Bar
            bar_start_x = 200
            bar_end_x = 1080
            bar_y = 655
            
            # Background Line (Gray)
            draw.line([(bar_start_x, bar_y), (bar_end_x, bar_y)], fill=(80, 80, 80), width=4)
            # Active Line (White - Showing random progress e.g. 30%)
            progress_end = bar_start_x + 150 # Static visuals ke liye bas thoda sa bhara hua dikhaya hai
            draw.line([(bar_start_x, bar_y), (progress_end, bar_y)], fill=(255, 255, 255), width=4)
            # Dot at the end of progress
            draw.ellipse((progress_end - 6, bar_y - 6, progress_end + 6, bar_y + 6), fill=(255, 255, 255))

            # Timestamps
            draw.text((bar_start_x - 60, bar_y - 15), "0:00", font=self.font_small, fill=(200,200,200))
            draw.text((bar_end_x + 20, bar_y - 15), song.duration, font=self.font_small, fill=(200,200,200))

            # 6. "Toxic Bots" Branding (Top Right Corner - Professional Badge style)
            # Badge Background
            branding_text = "TOXIC BOTS"
            brand_w = draw.textlength(branding_text, font=self.font_small)
            brand_padding = 15
            brand_bg_rect = [
                self.width - brand_w - (brand_padding * 2) - 30, 
                30, 
                self.width - 30, 
                30 + 35
            ]
            draw.rounded_rectangle(brand_bg_rect, radius=10, fill=(255, 50, 50)) # Premium Red
            
            # Badge Text
            draw.text(
                (brand_bg_rect[0] + brand_padding, 32),
                branding_text,
                font=self.font_small,
                fill=(255, 255, 255)
            )

            # Final Save
            background.save(output)
            
            if os.path.exists(temp):
                os.remove(temp)

            return output

        except Exception as e:
            print(f"[Thumbnail Error] {e}")
            return config.DEFAULT_THUMB
        
