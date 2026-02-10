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
        self.width = 1280
        self.height = 720

        self.color_white = (255, 255, 255)
        self.color_grey = (170, 170, 170)
        self.color_accent = (0, 255, 200)   # Neon 😎

        try:
            self.font_title = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 48)
            self.font_artist = ImageFont.truetype("Dev/helpers/Raleway-Bold.ttf", 32)
            self.font_small = ImageFont.truetype("Dev/helpers/Inter-Light.ttf", 22)
        except:
            self.font_title = ImageFont.load_default()
            self.font_artist = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                open(output_path, "wb").write(await resp.read())
            return output_path

    def draw_icons(self, draw, x, y):
        # Previous
        draw.polygon([(x, y), (x + 15, y - 10), (x + 15, y + 10)], fill=self.color_white)
        draw.polygon([(x + 15, y), (x + 30, y - 10), (x + 30, y + 10)], fill=self.color_white)

        # Pause
        px = x + 70
        draw.rounded_rectangle((px, y - 15, px + 8, y + 15), radius=2, fill=self.color_white)
        draw.rounded_rectangle((px + 16, y - 15, px + 24, y + 15), radius=2, fill=self.color_white)

        # Next
        nx = x + 130
        draw.polygon([(nx, y - 10), (nx + 15, y), (nx, y + 10)], fill=self.color_white)
        draw.polygon([(nx + 15, y - 10), (nx + 30, y), (nx + 15, y + 10)], fill=self.color_white)

    async def generate(self, song: Track) -> str:
        try:
            if not os.path.exists("cache"):
                os.makedirs("cache")

            temp = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}_final.png"

            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)

            # =========================
            # 🔥 AUTO COOL BACKGROUND
            # =========================
            base = Image.new("RGBA", (self.width, self.height), (10, 10, 20, 255))
            bg_draw = ImageDraw.Draw(base)

            bg_draw.rounded_rectangle(
                (30, 25, 1250, 695),
                radius=40,
                fill=(22, 22, 40, 255)
            )

            glow = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow)
            glow_draw.rounded_rectangle(
                (30, 25, 1250, 695),
                radius=40,
                outline=(0, 255, 200, 140),
                width=3
            )
            glow = glow.filter(ImageFilter.GaussianBlur(8))
            base = Image.alpha_composite(base, glow)

            # =========================
            # BLUR BACK ART
            # =========================
            original_art = Image.open(temp).convert("RGBA")

            screen_w, screen_h = 1100, 600
            blur_bg = original_art.resize((screen_w, screen_h), Image.Resampling.LANCZOS)
            blur_bg = blur_bg.filter(ImageFilter.GaussianBlur(30))
            blur_bg = ImageEnhance.Brightness(blur_bg).enhance(0.35)

            base.paste(blur_bg, (90, 60))

            # =========================
            # MAIN ALBUM ART
            # =========================
            art_size = (320, 320)
            art = ImageOps.fit(original_art, art_size, method=Image.Resampling.LANCZOS)

            mask = Image.new("L", art_size, 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.rounded_rectangle((0, 0, 320, 320), radius=30, fill=255)

            base.paste(art, (170, 200), mask)

            draw = ImageDraw.Draw(base)
            text_x = 540
            center_y = 260

            title = song.title
            if len(title) > 22:
                title = title[:22] + "..."

            # =========================
            # TEXT
            # =========================
            draw.text((text_x, center_y), title, font=self.font_title, fill=self.color_white)
            draw.text(
                (text_x, center_y + 65),
                "Toxic Bots",
                font=self.font_artist,
                fill=self.color_accent
            )

            # =========================
            # PROGRESS BAR
            # =========================
            bar_x = text_x
            bar_y = center_y + 140
            bar_length = 520

            draw.line([(bar_x, bar_y), (bar_x + bar_length, bar_y)], fill=(90, 90, 90), width=4)
            draw.line([(bar_x, bar_y), (bar_x + 190, bar_y)], fill=self.color_accent, width=4)
            draw.ellipse((bar_x + 183, bar_y - 7, bar_x + 199, bar_y + 7), fill=self.color_accent)

            draw.text((bar_x, bar_y + 18), "0:45", font=self.font_small, fill=self.color_grey)
            draw.text((bar_x + bar_length - 45, bar_y + 18), "3:12", font=self.font_small, fill=self.color_grey)

            # =========================
            # PLAYER ICONS
            # =========================
            icon_y = bar_y + 80
            icon_start_x = text_x + 120
            self.draw_icons(draw, icon_start_x, icon_y)

            base.save(output)

            if os.path.exists(temp):
                os.remove(temp)

            return output

        except Exception as e:
            print(f"Thumbnail Error: {e}")
            return config.DEFAULT_THUMB
