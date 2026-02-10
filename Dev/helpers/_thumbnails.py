import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        self.width = 1280
        self.height = 720
        self.fill = (255, 255, 255)
        self.secondary_fill = (200, 200, 200) 
        self.accent_color = (0, 255, 127)

        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Poppins-Bold.ttf", 45)
            self.font_artist = ImageFont.truetype("Dev/helpers/Poppins-Medium.ttf", 30)
            self.font_small = ImageFont.truetype("Dev/helpers/Poppins-Light.ttf", 20)
            self.font_logo = ImageFont.truetype("Dev/helpers/Poppins-ExtraBold.ttf", 40)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_small = ImageFont.load_default()
            self.font_logo = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    def draw_player_icons(self, draw, center_x, center_y):
        draw.rounded_rectangle((center_x - 12, center_y - 20, center_x - 4, center_y + 20), radius=4, fill=self.fill)
        draw.rounded_rectangle((center_x + 4, center_y - 20, center_x + 12, center_y + 20), radius=4, fill=self.fill)

        prev_x = center_x - 80
        draw.polygon([(prev_x, center_y), (prev_x + 20, center_y - 15), (prev_x + 20, center_y + 15)], fill=self.fill)
        draw.polygon([(prev_x - 15, center_y), (prev_x + 5, center_y - 15), (prev_x + 5, center_y + 15)], fill=self.fill)

        next_x = center_x + 80
        draw.polygon([(next_x, center_y), (next_x - 20, center_y - 15), (next_x - 20, center_y + 15)], fill=self.fill)
        draw.polygon([(next_x + 15, center_y), (next_x - 5, center_y - 15), (next_x - 5, center_y + 15)], fill=self.fill)

        vol_x = center_x - 130
        vol_y = center_y + 90
        draw.polygon([(vol_x, vol_y), (vol_x + 8, vol_y - 8), (vol_x + 8, vol_y + 8)], fill=self.secondary_fill)
        draw.rectangle((vol_x - 4, vol_y - 4, vol_x, vol_y + 4), fill=self.secondary_fill)
        draw.line([(vol_x + 20, vol_y), (vol_x + 260, vol_y)], fill=(100, 100, 100), width=3)
        draw.line([(vol_x + 20, vol_y), (vol_x + 180, vol_y)], fill=self.fill, width=3)
        draw.ellipse((vol_x + 175, vol_y - 5, vol_x + 185, vol_y + 5), fill=self.fill)
        
        list_x = center_x + 180
        list_y = center_y + 90
        draw.line([(list_x, list_y - 8), (list_x + 25, list_y - 8)], fill=self.secondary_fill, width=2)
        draw.line([(list_x, list_y), (list_x + 25, list_y)], fill=self.secondary_fill, width=2)
        draw.line([(list_x, list_y + 8), (list_x + 25, list_y + 8)], fill=self.secondary_fill, width=2)

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_boosted.png"
            
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            
            original = Image.open(temp).convert("RGBA")
            
            background = original.resize((self.width, self.height), Image.Resampling.LANCZOS)
            background = background.filter(ImageFilter.GaussianBlur(50))
            background = ImageEnhance.Brightness(background).enhance(0.35) 
            background = ImageEnhance.Contrast(background).enhance(1.2)

            art_size = (480, 480)
            art = ImageOps.fit(original, art_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            shadow = Image.new("RGBA", (art_size[0] + 40, art_size[1] + 40), (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.rounded_rectangle((20, 20, art_size[0]+20, art_size[1]+20), radius=45, fill=(0, 0, 0, 120))
            shadow = shadow.filter(ImageFilter.GaussianBlur(15))
            background.paste(shadow, (80, 90), shadow)

            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=40, fill=255)
            art.putalpha(mask)
            
            background.paste(art, (100, 110), art)

            draw = ImageDraw.Draw(background)
            
            text_x = 640
            center_control_x = text_x + (1280 - text_x) // 2 

            draw.text((1050, 50), "ToxicBots", font=self.font_logo, fill=self.accent_color)
            
            title = song.title
            if len(title) > 35:
                title = title[:35] + "..."
            
            shadow_offset = 2
            draw.text((text_x + shadow_offset, 200 + shadow_offset), title, font=self.font_title, fill=(0,0,0))
            draw.text((text_x, 200), title, font=self.font_title, fill=self.fill)
            
            channel = song.channel_name
            if len(channel) > 35:
                channel = channel[:35] + "..."
            draw.text((text_x, 270), channel, font=self.font_artist, fill=self.secondary_fill)

            bar_y = 360
            draw.line([(text_x, bar_y), (1200, bar_y)], fill=(80, 80, 80), width=4) 
            draw.line([(text_x, bar_y), (text_x + 220, bar_y)], fill=self.accent_color, width=4)
            draw.ellipse((text_x + 212, bar_y - 6, text_x + 228, bar_y + 6), fill=self.fill)

            draw.text((text_x, bar_y + 15), "0:00", font=self.font_small, fill=self.secondary_fill)
            draw.text((1150, bar_y + 15), song.duration, font=self.font_small, fill=self.secondary_fill)

            self.draw_player_icons(draw, center_control_x, 500)

            background.save(output)
            if os.path.exists(temp):
                os.remove(temp)
                
            return output
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return config.DEFAULT_THUMB
          
