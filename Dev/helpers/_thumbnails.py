import os
import sys
import asyncio
import aiohttp
from PIL import (
    Image, ImageDraw, ImageEnhance,
    ImageFilter, ImageFont, ImageOps
)

# Python 3.10 fix for lyricsgenius
if sys.version_info < (3, 11):
    import typing
    try:
        from typing_extensions import Self
    except ImportError:
        # Fallback agar typing_extensions installed nahi hai
        Self = typing.Any 
    typing.Self = Self

import lyricsgenius
from Dev import config
from Dev.helpers import Track

# ==========================================
# ⚙️ CONFIGURATION
# ==========================================
# Aapka provided token maine yahan laga diya hai
GENIUS_API_TOKEN = "f56PvHz_YPP03fyGVHfn2fgM0f5G_xwgmojUb7nEPnAGAgVBL1u-_X6vE36V1UqW"

class Thumbnail:
    def __init__(self):
        self.width = 1280
        self.height = 720
        
        # --- COLORS (Clean Theme) ---
        self.color_white = (255, 255, 255, 255)      # Pure White
        self.color_dim = (255, 255, 255, 180)        # Slightly Faded White
        self.color_faded = (255, 255, 255, 100)      # Very Faded White
        self.color_accent = (0, 255, 230)            # Neon Cyan/Green (Toxic Vibe)
        self.color_bg_overlay = (0, 0, 0, 160)       # Dark overlay for better text visibility

        # --- FONTS (Size Adjusted) ---
        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 45)
            self.font_artist = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 30)
            # Lyrics Font size chota kar diya (30px)
            self.font_lyrics = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 30) 
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 22)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_lyrics = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

        # Initialize Genius
        self.genius = lyricsgenius.Genius(GENIUS_API_TOKEN)
        self.genius.verbose = False
        self.genius.remove_section_headers = True

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                with open(output_path, "wb") as f:
                    f.write(await resp.read())
            return output_path

    def get_real_lyrics(self, query):
        try:
            # Title se "(Official Video)" wagarh hatane ki koshish
            clean_query = query.split("(")[0].split("-")[0].strip()
            song = self.genius.search_song(clean_query)
            
            if song and song.lyrics:
                # Lyrics cleaning
                lines = [l for l in song.lyrics.split('\n') if l.strip() and "Contributors" not in l and "Embed" not in l and "[" not in l]
                return lines[:15] # Top 15 lines only
            return self.get_fake_lyrics(query)
        except:
            return self.get_fake_lyrics(query)

    def get_fake_lyrics(self, title):
        return [
            "Lyrics unavailable...",
            f"Now Playing: {title}",
            "Feel the beat 🎧",
            "Toxic Bots Music",
            "Stereo Sound",
            "Pure Bass Boost",
            "Vibe Check: Passed",
            "Volume Up 🔊",
            "Enjoy the Rhythm"
        ]

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp_dl = f"cache/temp_{song.id}.jpg"
            # Output ab GIF hoga
            output_gif = f"cache/{song.id}_live.gif"

            if os.path.exists(output_gif):
                return output_gif

            await self.save_thumb(temp_dl, song.thumbnail)

            # ==========================================
            # 1. BACKGROUND GENERATION (Smooth Blur)
            # ==========================================
            original_art = Image.open(temp_dl).convert("RGBA")
            
            # Resize for background (Full HD)
            bg = original_art.resize((self.width, self.height), Image.Resampling.LANCZOS)
            
            # Heavy Blur (Smooth gradient look)
            bg = bg.filter(ImageFilter.GaussianBlur(radius=60))
            
            # Dark Overlay apply karo taaki text pop ho
            overlay = Image.new("RGBA", bg.size, self.color_bg_overlay)
            base_bg = Image.alpha_composite(bg, overlay)

            # ==========================================
            # 2. LEFT SIDE ELEMENTS (Static)
            # ==========================================
            
            # Album Art (Rounded Square)
            art_size = (360, 360)
            art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS)
            
            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, art_size[0], art_size[1]), radius=30, fill=255)
            
            # Create a frame to draw static elements
            static_frame = base_bg.copy()
            
            # Paste Art
            art_x, art_y = 100, 130
            static_frame.paste(art, (art_x, art_y), mask)
            
            draw = ImageDraw.Draw(static_frame)
            
            # Title & Info
            text_x = art_x
            text_y = art_y + 380
            
            title_text = song.title
            if len(title_text) > 20: title_text = title_text[:20] + "..."
            
            draw.text((text_x, text_y), title_text, font=self.font_title, fill=self.color_white)
            draw.text((text_x, text_y + 60), "Toxic Bots", font=self.font_artist, fill=self.color_accent)
            
            # Duration Bar (Simple)
            draw.rounded_rectangle((text_x, text_y + 110, text_x + 100, text_y + 140), radius=10, fill=(255,255,255,30))
            draw.text((text_x + 15, text_y + 113), "LIVE", font=self.font_small, fill=self.color_white)
            draw.text((text_x + 120, text_y + 113), "00:45 / 03:20", font=self.font_small, fill=self.color_dim)

            # Vertical Line Separator
            draw.line([(550, 100), (550, 620)], fill=(255, 255, 255, 50), width=2)

            # ==========================================
            # 3. RIGHT SIDE: LIVE LYRICS ANIMATION
            # ==========================================
            lyrics_list = self.get_real_lyrics(song.title)
            
            frames = []
            total_frames = 12 # Smoothness
            scroll_speed = 6
            
            lyrics_x = 600
            
            for i in range(total_frames):
                frame = static_frame.copy()
                d = ImageDraw.Draw(frame)
                
                # "Lyrics" Header
                d.text((lyrics_x, 80), "Lyrics", font=self.font_small, fill=self.color_accent)

                # Scroll Calculation
                start_y = 200 - (i * scroll_speed)
                
                for idx, line in enumerate(lyrics_list):
                    line_y = start_y + (idx * 60) # 60px gap (Reduced for smaller font)
                    
                    # Logic for Fading Text
                    # Center (approx 300-400px) is bright, edges are faded
                    if 250 < line_y < 450:
                        fill = self.color_white
                    elif 100 < line_y < 600:
                        fill = self.color_faded
                    else:
                        fill = (255,255,255,0) # Invisible
                        
                    # Only draw if visible on screen
                    if 80 < line_y < 650:
                        d.text((lyrics_x, line_y), line[:40], font=self.font_lyrics, fill=fill)
                
                frames.append(frame)

            # Save GIF
            frames[0].save(
                output_gif,
                save_all=True,
                append_images=frames[1:],
                optimize=True,
                duration=120, # Speed
                loop=0
            )

            if os.path.exists(temp_dl):
                os.remove(temp_dl)

            return output_gif

        except Exception as e:
            print(f"Thumbnail Error: {e}")
            return config.DEFAULT_THUMB
            
