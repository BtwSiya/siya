import os
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from Dev import config
from Dev.helpers import Track

class Thumbnail:
    def __init__(self):
        # कैनवास साइज (इसे मत छेड़ें)
        self.width = 1280
        self.height = 720
        
        # आपकी लैपटॉप वाली फोटो का नाम
        self.background_path = "Dev/helpers/bg.jpg" 

        # कलर सेटिंग्स
        self.text_color = (255, 255, 255) # White Text
        self.brand_color = (200, 200, 200) # Light Grey for "Toxic Bots"

        # फॉन्ट्स लोड करना
        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 50) # गाने का नाम
            self.font_brand = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 35) # Toxic Bots
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 25) # टाइमर (अगर चाहिए)
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
            # कैश डायरेक्टरी चेक
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_final.png"

            # अगर थंबनेल पहले से बना है तो वही भेजें
            if os.path.exists(output):
                return output

            # गाने का थंबनेल डाउनलोड करें
            await self.save_thumb(temp, song.thumbnail)
            
            # --- 1. बैकग्राउंड (लैपटॉप) सेट करें ---
            if os.path.exists(self.background_path):
                background = Image.open(self.background_path).convert("RGBA")
                background = background.resize((self.width, self.height), Image.Resampling.LANCZOS)
            else:
                # अगर background.jpg नहीं मिली तो ब्लैक स्क्रीन
                background = Image.new("RGBA", (self.width, self.height), (20, 20, 20, 255))

            # --- 2. लेफ्ट साइड: गाने की फोटो (Album Art) ---
            original_art = Image.open(temp).convert("RGBA")
            
            # फोटो को थोड़ा बड़ा और गोल कोनों वाला बनाएं
            art_size = (420, 420) 
            art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            
            # गोल कोने (Rounded Corners)
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=30, fill=255)
            art.putalpha(mask)

            # फोटो को लेफ्ट साइड में पेस्ट करें (Coordinates: X=100, Y=150)
            background.paste(art, (100, 150), art)

            # --- 3. राइट साइड: टेक्स्ट और ब्रांडिंग ---
            draw = ImageDraw.Draw(background)
            
            # ये Coordinates आपकी भेजी गई फोटो के हिसाब से सेट किए गए हैं
            text_x = 600       # राइट साइड की शुरुआत
            line_y = 300       # वो लाइन जो बैकग्राउंड में दिख रही है (लगभग)
            
            # A. गाने का नाम (लाइन के ऊपर)
            title = song.title
            if len(title) > 20:
                title = title[:20] + "..."
            
            # टेक्स्ट को थोड़ा ऊपर (Y = 230) ड्रा करें
            draw.text((text_x + 20, line_y - 70), title, font=self.font_title, fill=self.text_color)

            # B. Toxic Bots (लाइन के नीचे)
            draw.text((text_x + 20, line_y + 30), "Toxic Bots", font=self.font_brand, fill=self.brand_color)

            # C. डायनामिक प्रोग्रेस बार (ताकि लाइन "भरी हुई" दिखे)
            # हम बैकग्राउंड वाली लाइन के ऊपर एक सफेद लाइन ड्रा करेंगे
            bar_start_x = text_x
            bar_end_x = 1100
            
            # लाइन की पोजीशन फोटो के हिसाब से (Y=305 लगभग)
            draw.line([(bar_start_x, 305), (bar_end_x, 305)], fill=(80, 80, 80), width=6) # डार्क ग्रे बेस
            
            # वाइट प्रोग्रेस (मान लो 30% गाना चला है दिखाने के लिए)
            draw.line([(bar_start_x, 305), (bar_start_x + 150, 305)], fill=(255, 255, 255), width=6)
            draw.ellipse((bar_start_x + 140, 297, bar_start_x + 160, 313), fill=(255, 255, 255)) # Dot

            # ड्यूरेशन टेक्स्ट (बार के नीचे)
            draw.text((bar_start_x, 330), "0:00", font=self.font_small, fill=self.text_color)
            draw.text((bar_end_x - 50, 330), song.duration, font=self.font_small, fill=self.text_color)

            # फाइल सेव करें
            background.save(output)
            
            # टेम्परेरी फाइल डिलीट करें
            if os.path.exists(temp):
                os.remove(temp)
                
            return output
            
        except Exception as e:
            print(f"Error generating thumbnail: {e}")
            return config.DEFAULT_THUMB
          
