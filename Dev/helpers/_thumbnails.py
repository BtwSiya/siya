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
        self.background_path = "Dev/helpers/bg.jpg" 

        self.text_color = (255, 255, 255) # White
        self.brand_color = (220, 220, 220) # Light Grey

        # --- FONT SIZE FIX (Smaller) ---
        try:
            # टाइटल का फॉन्ट छोटा किया (50 -> 38)
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 38)
            # ब्रांड का फॉन्ट छोटा किया (35 -> 28)
            self.font_brand = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 28)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 20)
        except:
            self.font_title = ImageFont.load_default()
            self.font_brand = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_final_v2.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            
            # --- 1. Background ---
            if os.path.exists(self.background_path):
                background = Image.open(self.background_path).convert("RGBA")
                background = background.resize((self.width, self.height), Image.Resampling.LANCZOS)
            else:
                background = Image.new("RGBA", (self.width, self.height), (20, 20, 20, 255))

            # --- 2. Album Art (Left Side - Fixed Size & Position) ---
            original_art = Image.open(temp).convert("RGBA")
            
            # SIZE FIX: 420px से घटाकर 320px कर दिया ताकि फ्रेम से बाहर न जाए
            art_size = (320, 320) 
            art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            # Rounded Corners
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=25, fill=255)
            art.putalpha(mask)

            # POSITION FIX: X को 100 से बढ़ाकर 140 कर दिया ताकि लैपटॉप के किनारे से दूर रहे
            # Y को 200 कर दिया ताकि वर्टीकली सेंटर में दिखे
            background.paste(art, (140, 200), art)

            # --- 3. Text (Right Side) ---
            draw = ImageDraw.Draw(background)
            
            # Coordinates for Right Side (Based on your photo 817.jpg)
            # लाइन लगभग Y=300 पर है, इसलिए हम उसके हिसाब से टेक्स्ट सेट करेंगे
            
            text_start_x = 580 # टेक्स्ट यहाँ से शुरू होगा (लाइन की शुरुआत के पास)
            line_y_position = 295 # फोटो में लाइन यहाँ दिख रही है

            # A. Title (लाइन के ऊपर)
            title = song.title
            if len(title) > 25:
                title = title[:25] + "..."
            
            # Y=240 (लाइन से थोड़ा ऊपर)
            draw.text((text_start_x, line_y_position - 55), title, font=self.font_title, fill=self.text_color)

            # B. Toxic Bots (लाइन के नीचे)
            # Y=320 (लाइन के नीचे, लेकिन Play बटन से ऊपर)
            draw.text((text_start_x, line_y_position + 25), "Toxic Bots", font=self.font_brand, fill=self.brand_color)

            # Note: मैंने draw.line वाला कोड हटा दिया है।
            # अब सिर्फ "Toxic Bots" और Song Title दिखेगा, लाइन बैकग्राउंड वाली ही रहेगी।

            # Save
            background.save(output)
            
            if os.path.exists(temp):
                os.remove(temp)
                
            return output
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return config.DEFAULT_THUMB
          
