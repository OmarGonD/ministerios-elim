#!/usr/bin/env python3
"""Create the Ministerios Elim leadership deck with LibreOffice Impress."""

from __future__ import annotations

import hashlib
import os
import sys
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "presentacion"
WORK_DIR = Path("/tmp/ministerios-elim-ppt-assets")
LOGO = ROOT / "presentacion/capturas/logo-elim.png"
DEMO = ROOT / "static/img/demo"
DOCTRINA = ROOT / "home/fixtures/doctrina"
PROTOTYPE_SCREENSHOT = ROOT / "presentacion/capturas/doctrina-la-salvacion.png"

W, H = 33867, 19050
BLACK = 0x111111
INK = 0x242424
GOLD = 0xC5A059
GOLD_LIGHT = 0xE7D7AA
IVORY = 0xF7F3EA
WHITE = 0xFFFFFF
MUTED = 0x6D6A64
GREEN = 0x87C45B
CYAN = 0x36BBD3
RED = 0xA94A43
PALE_GREEN = 0xE7F1DD
PALE_CYAN = 0xDFF3F6
PALE_GOLD = 0xF2EAD5
FONT = "Liberation Sans"
SERIF = "Liberation Serif"


def crop_image(source: Path, width: int, height: int, *, focus=(0.5, 0.5)) -> Path:
    """Create a temporary image cropped to the requested aspect ratio."""
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(f"{source}:{width}:{height}:{focus}".encode()).hexdigest()[:14]
    target = WORK_DIR / f"{key}.jpg"
    if target.exists():
        return target
    with Image.open(source) as image:
        image = image.convert("RGB")
        target_ratio = width / height
        source_ratio = image.width / image.height
        if source_ratio > target_ratio:
            crop_width = int(image.height * target_ratio)
            left = int((image.width - crop_width) * focus[0])
            box = (left, 0, left + crop_width, image.height)
        else:
            crop_height = int(image.width / target_ratio)
            top = int((image.height - crop_height) * focus[1])
            box = (0, top, image.width, top + crop_height)
        image = image.crop(box)
        max_width = 1920
        if image.width > max_width:
            new_height = int(image.height * max_width / image.width)
            image = image.resize((max_width, new_height), Image.Resampling.LANCZOS)
        image.save(target, "JPEG", quality=90, optimize=True)
    return target


class Deck:
    """Small raster slide renderer; keeps PPT generation dependency-free."""

    PX_W, PX_H = 1920, 1080

    def __init__(self):
        self.pages = []
        self.commands = []
        self._command_map = {}
        self.slide_number = 0

    def _record(self, page, command):
        self._command_map[id(page)].append(command)

    @staticmethod
    def _rgb(color):
        return ((color >> 16) & 255, (color >> 8) & 255, color & 255)

    @classmethod
    def _box(cls, x, y, w, h):
        sx, sy = cls.PX_W / W, cls.PX_H / H
        return tuple(round(v) for v in (x * sx, y * sy, (x + w) * sx, (y + h) * sy))

    @staticmethod
    def _font_path(font, bold=False, italic=False):
        family = "LiberationSerif" if font == SERIF else "LiberationSans"
        style = "BoldItalic" if bold and italic else "Bold" if bold else "Italic" if italic else "Regular"
        return f"/usr/share/fonts/liberation/{family}-{style}.ttf"

    def slide(self, background=IVORY, *, dark=False):
        page = Image.new("RGB", (self.PX_W, self.PX_H), self._rgb(background))
        self.pages.append(page)
        page_commands = [{"type": "rect", "x": 0, "y": 0, "w": W, "h": H,
                          "fill": background, "line": background, "radius": 0,
                          "transparency": 0}]
        self.commands.append(page_commands)
        self._command_map[id(page)] = page_commands
        self.slide_number += 1
        if self.slide_number > 1:
            self.image(page, LOGO, W - 2600, 520, 1500, 680, fit="contain")
            self.text(
                page, W - 1300, H - 700, 700, 300, str(self.slide_number),
                8, WHITE if dark else MUTED, bold=True, align="right",
            )
        return page

    def drop_last_slide(self):
        """Remove a rendered slide and keep automatic numbering contiguous."""
        page = self.pages.pop()
        self.commands.pop()
        self._command_map.pop(id(page), None)
        self.slide_number -= 1

    def rect(self, page, x, y, w, h, fill, *, line=None, radius=0, transparency=0):
        self._record(page, {"type": "rect", "x": x, "y": y, "w": w, "h": h,
                            "fill": fill, "line": fill if line is None else line,
                            "radius": radius, "transparency": transparency})
        box = self._box(x, y, w, h)
        draw = ImageDraw.Draw(page, "RGBA")
        alpha = round(255 * (100 - transparency) / 100)
        fill_rgba = (*self._rgb(fill), alpha)
        outline = self._rgb(fill if line is None else line)
        r = round(radius * self.PX_W / W)
        draw.rounded_rectangle(box, radius=r, fill=fill_rgba, outline=outline, width=1)

    def line(self, page, x1, y1, x2, y2, color=GOLD, width=80):
        self._record(page, {"type": "line", "x1": x1, "y1": y1, "x2": x2,
                            "y2": y2, "color": color, "width": width})
        sx, sy = self.PX_W / W, self.PX_H / H
        ImageDraw.Draw(page).line(
            (round(x1 * sx), round(y1 * sy), round(x2 * sx), round(y2 * sy)),
            fill=self._rgb(color), width=max(1, round(width * sx)),
        )

    def text(
        self, page, x, y, w, h, value, size, color=INK, *, bold=False,
        font=FONT, align="left", valign="top", margin=0, italic=False,
    ):
        self._record(page, {"type": "text", "x": x, "y": y, "w": w, "h": h,
                            "value": str(value), "size": size, "color": color,
                            "bold": bold, "font": font, "align": align,
                            "valign": valign, "margin": margin, "italic": italic})
        draw = ImageDraw.Draw(page)
        left, top, right, bottom = self._box(x + margin, y + margin, w - 2 * margin, h - 2 * margin)
        px_size = max(10, round(size * 2.05))
        face = ImageFont.truetype(self._font_path(font, bold, italic), px_size)
        lines = []
        for paragraph in str(value).split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue
            current = words[0]
            for word in words[1:]:
                candidate = current + " " + word
                if draw.textlength(candidate, font=face) <= right - left:
                    current = candidate
                else:
                    lines.append(current)
                    current = word
            lines.append(current)
        spacing = max(2, round(px_size * 0.23))
        heights = [draw.textbbox((0, 0), line or "Ag", font=face)[3] for line in lines]
        total = sum(heights) + spacing * max(0, len(lines) - 1)
        cy = top if valign == "top" else top + max(0, (bottom - top - total) // 2) if valign == "center" else bottom - total
        for line, line_h in zip(lines, heights):
            line_w = draw.textlength(line, font=face)
            cx = left if align == "left" else left + (right - left - line_w) / 2 if align == "center" else right - line_w
            draw.text((round(cx), round(cy)), line, font=face, fill=self._rgb(color))
            cy += line_h + spacing

    def image(self, page, source: Path, x, y, w, h, *, fit="cover", focus=(0.5, 0.5)):
        source = Path(source)
        if not source.exists():
            return self.rect(page, x, y, w, h, PALE_GOLD, line=GOLD_LIGHT)
        left, top, right, bottom = self._box(x, y, w, h)
        out_w, out_h = right - left, bottom - top
        with Image.open(source) as opened:
            image = opened.convert("RGBA")
            if fit == "cover":
                target_ratio, source_ratio = out_w / out_h, image.width / image.height
                if source_ratio > target_ratio:
                    cw = round(image.height * target_ratio)
                    offset = round((image.width - cw) * focus[0])
                    image = image.crop((offset, 0, offset + cw, image.height))
                else:
                    ch = round(image.width / target_ratio)
                    offset = round((image.height - ch) * focus[1])
                    image = image.crop((0, offset, image.width, offset + ch))
                image = image.resize((out_w, out_h), Image.Resampling.LANCZOS)
                page.paste(image, (left, top), image)
                prepared = crop_image(source, int(w), int(h), focus=focus)
                self._record(page, {"type": "image", "source": prepared,
                                    "x": x, "y": y, "w": w, "h": h})
            else:
                image.thumbnail((out_w, out_h), Image.Resampling.LANCZOS)
                px = left + (out_w - image.width) // 2
                py = top + (out_h - image.height) // 2
                page.paste(image, (px, py), image)
                sx, sy = self.PX_W / W, self.PX_H / H
                actual_x, actual_y = px / sx, py / sy
                actual_w, actual_h = image.width / sx, image.height / sy
                self._record(page, {"type": "image", "source": source,
                                    "x": actual_x, "y": actual_y,
                                    "w": actual_w, "h": actual_h})

    def title(self, page, kicker, heading, *, dark=False, sub=None):
        color = WHITE if dark else INK
        self.text(page, 1600, 850, 27000, 500, kicker.upper(), 10, GOLD, bold=True)
        self.text(page, 1600, 1450, 29000, 1800, heading, 27, color, bold=True, font=SERIF)
        if sub:
            self.text(page, 1600, 3200, 29000, 800, sub, 12, WHITE if dark else MUTED)
        self.line(page, 1600, 4000 if sub else 3400, 5000, 4000 if sub else 3400, GOLD, 90)

    def card(self, page, x, y, w, h, heading, body, *, accent=GOLD, fill=WHITE, icon=None):
        self.rect(page, x, y, w, h, fill, line=GOLD_LIGHT, radius=180)
        self.rect(page, x, y, 140, h, accent, line=accent)
        if icon:
            self.text(page, x + 500, y + 300, 900, 800, icon, 24, accent, bold=True, valign="center")
            tx = x + 1500
        else:
            tx = x + 600
        self.text(page, tx, y + 350, w - (tx - x) - 400, 650, heading, 15, INK, bold=True)
        self.text(page, x + 600, y + 1200, w - 1100, h - 1500, body, 10.5, MUTED)

    def pill(self, page, x, y, w, text, color=GOLD, fill=BLACK):
        self.rect(page, x, y, w, 650, fill, line=fill, radius=300)
        self.text(page, x + 180, y + 80, w - 360, 450, text, 9, color, bold=True, align="center", valign="center")


def build_deck(deck: Deck):
    # 1 — Cover
    page = deck.slide(BLACK, dark=True)
    deck.image(page, DEMO / "inicio.png", 0, 0, W, H, fit="cover", focus=(0.52, 0.45))
    deck.rect(page, 0, 0, W, H, BLACK, transparency=30)
    deck.rect(page, 0, 0, 14500, H, BLACK, transparency=8)
    deck.image(page, LOGO, 1800, 1150, 3000, 1500, fit="contain")
    deck.text(page, 1800, 4400, 13800, 4300,
              "UNA PLATAFORMA\nDIGITAL PARA\nFORMAR, CONECTAR\nY SERVIR", 24, WHITE,
              bold=True, font=SERIF)
    deck.line(page, 1800, 9000, 6000, 9000, GOLD, 120)
    deck.text(page, 1800, 9550, 12500, 1500,
              "Propuesta para el liderazgo de Ministerios Elim", 16, GOLD_LIGHT, bold=True)
    deck.text(page, 1800, 11200, 12000, 1300,
              "Prototipo funcional · Red de iglesias · Formación doctrinal · Comunidad", 11, WHITE)
    deck.text(page, 1800, H - 1450, 9000, 500, "14 de octubre de 2026", 10, WHITE)

    # 2 — Executive thesis
    page = deck.slide(IVORY)
    deck.title(page, "Tesis ejecutiva", "De sitio informativo a plataforma ministerial")
    deck.text(page, 1600, 4300, 13500, 4400,
              "El sitio actual representa muy bien a la congregación de Los Ángeles. "
              "El prototipo amplía esa presencia hacia una plataforma que puede servir a toda la red.",
              21, INK, bold=True, font=SERIF)
    deck.text(page, 1600, 9200, 13200, 3100,
              "La propuesta conserva identidad, predicación, horarios y conexión; añade estructura doctrinal, "
              "perfiles, permisos, directorio vivo, materiales, eventos y participación.", 13, MUTED)
    pillars = [
        ("01", "Formar", "Rutas de doctrina y recursos reutilizables", GREEN),
        ("02", "Conectar", "Iglesias, pastores, miembros y visitantes", CYAN),
        ("03", "Gobernar", "Roles claros y publicación con permisos", GOLD),
        ("04", "Escalar", "Una base común para múltiples ciudades y países", RED),
    ]
    for i, (num, head, body, color) in enumerate(pillars):
        y = 4200 + i * 3000
        deck.rect(page, 17100, y, 14000, 2300, WHITE, line=GOLD_LIGHT, radius=180)
        deck.text(page, 17800, y + 400, 1600, 800, num, 19, color, bold=True)
        deck.text(page, 19800, y + 350, 3600, 700, head, 16, INK, bold=True)
        deck.text(page, 23400, y + 420, 6900, 1050, body, 10.5, MUTED)
    deck.text(page, 1600, H - 900, 29000, 400,
              "Comparación de alcances distintos: congregación local actual vs. plataforma propuesta para la red.", 8.5, MUTED, italic=True)

    # 3–7 — Visual tour of the local prototype
    def browser_shell(page, url):
        x, y, w, h = 1200, 4300, 22600, 12700
        deck.rect(page, x, y, w, h, WHITE, line=0xD4D0C8, radius=220)
        deck.rect(page, x, y, w, 1050, 0x262626, line=0x262626, radius=220)
        for i, color in enumerate((0xE36B62, 0xE8BD55, 0x69C26A)):
            deck.rect(page, x + 400 + i * 420, y + 360, 210, 210, color, line=color, radius=100)
        deck.rect(page, x + 1900, y + 230, w - 2400, 570, 0x3C3C3C, line=0x555555, radius=250)
        deck.text(page, x + 2350, y + 330, w - 3300, 300, url, 8.5, 0xE8E8E8, valign="center")
        nav_y = y + 1050
        deck.rect(page, x, nav_y, w, 1250, WHITE, line=0xE9E5DC)
        deck.image(page, LOGO, x + 500, nav_y + 230, 1250, 700, fit="contain")
        deck.text(page, x + 2350, nav_y + 360, 11200, 450,
                  "Quiénes Somos     Doctrina     Foros     Iglesias     Materiales", 8.8, INK, bold=True)
        deck.rect(page, x + w - 4000, nav_y + 260, 3200, 700, PALE_GOLD, line=GOLD, radius=120)
        deck.text(page, x + w - 3750, nav_y + 410, 2700, 350, "INICIAR SESIÓN", 8, GOLD, bold=True, align="center")
        return x, nav_y + 1250, w, h - 2300

    def notes(page, heading, items, accent=GOLD):
        deck.text(page, 25200, 4700, 6800, 750, heading.upper(), 11, accent, bold=True)
        for i, item in enumerate(items):
            y = 5900 + i * 2550
            deck.rect(page, 25000, y, 7100, 1950, WHITE, line=GOLD_LIGHT, radius=140)
            deck.rect(page, 25000, y, 180, 1950, accent, line=accent)
            deck.text(page, 25600, y + 330, 5900, 1200, item, 9.8, INK, bold=True, valign="center")

    page = deck.slide(IVORY)
    deck.title(page, "Recorrido visual", "Una portada que explica quiénes somos y qué hacer")
    x, y, w, h = browser_shell(page, "ministerioselim.org/")
    deck.image(page, DEMO / "inicio.png", x, y, w, h, fit="cover", focus=(0.52, 0.48))
    deck.rect(page, x, y, w, h, BLACK, transparency=42)
    deck.image(page, LOGO, x + 1300, y + 900, 2600, 1250, fit="contain")
    deck.text(page, x + 1300, y + 3100, 12500, 1900,
              "Una iglesia para conocer a Cristo,\ncrecer y servir", 23, WHITE, bold=True, font=SERIF)
    deck.text(page, x + 1350, y + 5500, 11200, 900,
              "Encuentra una iglesia, conoce nuestra doctrina y participa de la comunidad.", 11, WHITE)
    deck.rect(page, x + 1350, y + 7000, 4600, 900, GOLD, line=GOLD, radius=140)
    deck.text(page, x + 1650, y + 7190, 4000, 450, "CONOCER MÁS", 9, BLACK, bold=True, align="center")
    notes(page, "La mejora visible", ["Mensaje y siguiente paso claros", "Acceso directo a doctrina e iglesias", "Diseño coherente en toda la experiencia"], GREEN)

    page = deck.slide(IVORY)
    deck.title(page, "Recorrido visual", "Doctrina presentada como una biblioteca de formación")
    x, y, w, h = browser_shell(page, "ministerioselim.org/doctrina/")
    deck.rect(page, x, y, w, 3000, BLACK, line=BLACK)
    deck.text(page, x + 900, y + 700, w - 1800, 800, "Doctrina", 25, GOLD, bold=True, font=SERIF, align="center")
    deck.text(page, x + 2100, y + 1700, w - 4200, 650,
              "Aprende a tu ritmo y profundiza en los fundamentos de la fe", 10.5, WHITE, align="center")
    levels = [
        ("BÁSICA", "Fundamentos para comenzar", DOCTRINA / "la-salvacion.png", GREEN),
        ("INTERMEDIA", "Vida cristiana y Espíritu Santo", DOCTRINA / "el-espiritu-santo.png", CYAN),
        ("AVANZADA", "Estudio y panorama bíblico", DOCTRINA / "panorama-escatologico.png", GOLD),
    ]
    for i, (head, body, img, color) in enumerate(levels):
        cx = x + 650 + i * 7300
        deck.rect(page, cx, y + 3500, 6650, 6100, WHITE, line=GOLD_LIGHT, radius=150)
        deck.image(page, img, cx, y + 3500, 6650, 3000, fit="cover")
        deck.text(page, cx + 400, y + 6900, 5850, 500, head, 11, color, bold=True, align="center")
        deck.text(page, cx + 550, y + 7650, 5550, 900, body, 9.2, MUTED, align="center")
        deck.text(page, cx + 550, y + 8750, 5550, 450, "VER LECCIONES  →", 8, INK, bold=True, align="center")
    notes(page, "Lo que permite", ["Tres niveles con rutas comprensibles", "Entradas con autor, recursos y referencias", "Contenido administrable desde Wagtail"], GOLD)

    page = deck.slide(IVORY)
    deck.title(page, "Recorrido visual", "Cada iglesia obtiene una presencia local completa")
    x, y, w, h = browser_shell(page, "ministerioselim.org/peru/lima/elim-demo/")
    deck.image(page, DEMO / "iglesia-lima.png", x, y, w, 5600, fit="cover")
    deck.rect(page, x, y, w, 5600, BLACK, transparency=45)
    deck.text(page, x + 1000, y + 2350, w - 2000, 900, "Elim Lima", 27, WHITE, bold=True, font=SERIF, align="center")
    deck.text(page, x + 2200, y + 3450, w - 4400, 550,
              "Horarios · ubicación · contacto · eventos", 10, GOLD_LIGHT, bold=True, align="center")
    deck.rect(page, x + 800, y + 6400, 6500, 2700, WHITE, line=GOLD_LIGHT, radius=150)
    deck.image(page, DEMO / "pastor-lima.png", x + 1100, y + 6750, 1850, 1850, fit="cover", focus=(0.5, 0.2))
    deck.text(page, x + 3400, y + 6800, 3400, 500, "Pastor local", 11, GOLD, bold=True)
    deck.text(page, x + 3400, y + 7500, 3300, 900, "Perfil, contacto y responsabilidad visible", 8.7, MUTED)
    for i, label in enumerate(("PRÓXIMOS EVENTOS", "PREDICACIONES", "MATERIALES")):
        bx = x + 8000 + (i % 2) * 6500
        by = y + 6400 + (i // 2) * 1600
        deck.rect(page, bx, by, 5900, 1250, PALE_GOLD if i == 0 else WHITE, line=GOLD_LIGHT, radius=130)
        deck.text(page, bx + 350, by + 400, 5200, 450, label, 8.5, INK, bold=True, align="center")
    notes(page, "Una ficha viva", ["Información local actualizable", "Pastor y responsables identificados", "Eventos y recursos propios"], CYAN)

    page = deck.slide(IVORY)
    deck.title(page, "Recorrido visual", "La cobertura se convierte en un directorio fácil de explorar")
    x, y, w, h = browser_shell(page, "ministerioselim.org/iglesias/")
    deck.rect(page, x, y, w, 2500, BLACK, line=BLACK)
    deck.text(page, x + 900, y + 650, w - 1800, 750, "Nuestras Iglesias", 24, GOLD, bold=True, font=SERIF, align="center")
    deck.text(page, x + 2100, y + 1550, w - 4200, 450, "Encuentra una congregación por país y ciudad", 9.5, WHITE, align="center")
    churches = [("LIMA, PERÚ", "iglesia-lima.png"), ("AREQUIPA, PERÚ", "iglesia-arequipa.png"), ("MADRID, ESPAÑA", "iglesia-madrid.png")]
    for i, (label, filename) in enumerate(churches):
        cx = x + 600 + i * 7350
        deck.rect(page, cx, y + 3200, 6750, 6200, WHITE, line=GOLD_LIGHT, radius=150)
        deck.image(page, DEMO / filename, cx, y + 3200, 6750, 3600, fit="cover")
        deck.text(page, cx + 450, y + 7150, 5850, 500, label, 10.5, INK, bold=True, align="center")
        deck.text(page, cx + 600, y + 7900, 5550, 550, "Ver iglesia, horarios y actividades", 8.5, MUTED, align="center")
        deck.text(page, cx + 600, y + 8650, 5550, 400, "ABRIR FICHA  →", 8, GOLD, bold=True, align="center")
    notes(page, "Más útil que una lista", ["Búsqueda visual por ubicación", "Una estructura común para toda la red", "Preparado para añadir nuevas ciudades"], GREEN)

    page = deck.slide(IVORY)
    deck.title(page, "Recorrido visual", "Miembros y líderes encuentran sus herramientas en un solo lugar")
    x, y, w, h = browser_shell(page, "ministerioselim.org/miembros/dashboard/")
    deck.rect(page, x, y, w, 2900, BLACK, line=BLACK)
    deck.text(page, x + 850, y + 700, 13000, 650, "Bienvenido, Samuel", 21, WHITE, bold=True, font=SERIF)
    deck.text(page, x + 850, y + 1550, 13500, 500, "Tu espacio para aprender, participar y servir", 9.5, GOLD_LIGHT)
    deck.image(page, DEMO / "miembro.png", x + w - 3300, y + 450, 2200, 2200, fit="cover", focus=(0.5, 0.2))
    actions = [
        ("MI PERFIL", "Datos y participación", GOLD), ("DOCTRINA", "Continuar aprendiendo", GREEN),
        ("DIRECTORIO", "Encontrar una iglesia", CYAN), ("FOROS", "Conversar con la comunidad", RED),
        ("EVENTOS", "Próximas actividades", 0x7B5EA7), ("MATERIALES", "Recursos para servir", 0x3F6D78),
    ]
    for i, (head, body, color) in enumerate(actions):
        cx = x + 650 + (i % 3) * 7200
        cy = y + 3550 + (i // 3) * 3000
        deck.rect(page, cx, cy, 6550, 2450, WHITE, line=GOLD_LIGHT, radius=150)
        deck.rect(page, cx, cy, 850, 2450, color, line=color)
        deck.text(page, cx + 1250, cy + 420, 4700, 450, head, 10, color, bold=True)
        deck.text(page, cx + 1250, cy + 1120, 4700, 650, body, 8.8, MUTED)
    notes(page, "Valor cotidiano", ["Acceso según el rol de cada persona", "Formación, comunidad y recursos conectados", "Base para participación y seguimiento"], RED)

    # 3 — Current strengths
    page = deck.slide(BLACK, dark=True)
    deck.title(page, "Punto de partida", "Lo que el sitio actual ya hace bien", dark=True,
               sub="Una presencia pública centrada en identidad, predicación y conexión congregacional")
    strengths = [
        ("IDENTIDAD", "Historia, misión, visión, credo y liderazgo."),
        ("SERVICIOS", "Horarios presenciales y transmisión en línea."),
        ("PREDICACIÓN", "Biblioteca visible de mensajes en video."),
        ("CONEXIÓN", "Eventos, contacto, ofrendas, radio y redes."),
        ("COBERTURA", "Amplio listado de iglesias en EE. UU. y otros países."),
    ]
    for i, (head, body) in enumerate(strengths):
        x = 1600 + (i % 3) * 10100
        y = 5200 + (i // 3) * 4300
        w = 9100 if i < 3 else 14200
        if i == 4:
            x = 17000
        deck.rect(page, x, y, w, 3300, 0x202020, line=0x3A3A3A, radius=160)
        deck.text(page, x + 600, y + 500, w - 1200, 650, head, 13, GOLD, bold=True)
        deck.text(page, x + 600, y + 1350, w - 1200, 1300, body, 11, WHITE)
    deck.text(page, 1600, H - 1200, 29000, 500,
              "Fuente: ministerioselimlosangeles.net, revisión pública del 14/10/2026", 8.5, GOLD_LIGHT)

    # 4 — Opportunity
    page = deck.slide(IVORY)
    deck.title(page, "Oportunidad", "Convertir el directorio en una red digital viva")
    deck.text(page, 1600, 4300, 13500, 1700,
              "El sitio actual enumera una cobertura internacional extensa. Esa escala abre una oportunidad: "
              "que cada iglesia tenga información verificable, responsable y actualizable.", 16, INK, bold=True)
    deck.card(page, 1600, 6900, 13500, 3000, "Hoy: directorio público",
              "Listas de ubicaciones agrupadas por región. La actualización depende de editar páginas centrales.", accent=GOLD)
    deck.card(page, 1600, 10400, 13500, 3000, "Propuesta: fichas vivas",
              "País → ciudad → iglesia, con pastor, horarios, dirección, eventos, sermones y materiales.", accent=GREEN)
    deck.image(page, DEMO / "iglesia-lima.png", 17000, 4300, 14300, 9300, fit="cover")
    deck.rect(page, 17000, 11500, 14300, 2100, BLACK, transparency=12)
    deck.text(page, 17800, 11900, 12700, 650, "UNA PÁGINA PARA CADA IGLESIA", 16, WHITE, bold=True)
    deck.text(page, 17800, 12600, 12700, 500, "Identidad común, información local y administración delegada", 9.5, GOLD_LIGHT)
    deck.drop_last_slide()

    # 5 — Matrix
    page = deck.slide(WHITE)
    deck.title(page, "Comparación", "Dos experiencias digitales, dos alcances")
    rows = [
        ("Propósito", "Presencia pública de Elim Los Ángeles", "Plataforma para congregación y red"),
        ("Doctrina", "Creencias y material publicado", "Niveles, lecciones, referencias y recursos"),
        ("Iglesias", "Directorio agrupado por regiones", "Fichas navegables por país y ciudad"),
        ("Usuarios", "Experiencia principalmente pública", "Visitante, miembro, pastor, supervisor y apóstol"),
        ("Publicación", "Edición central del sitio", "Permisos y responsabilidad distribuida"),
        ("Comunidad", "Contacto, redes y eventos", "Perfiles, foros, comentarios y paneles"),
        ("Escalabilidad", "Páginas y listas administradas manualmente", "Modelos reutilizables y búsquedas"),
    ]
    x0, y0 = 1600, 4300
    widths = [5500, 11900, 13300]
    headers = ["DIMENSIÓN", "SITIO ACTUAL", "PROTOTIPO PROPUESTO"]
    x = x0
    for w, value in zip(widths, headers):
        deck.rect(page, x, y0, w, 1000, BLACK, line=WHITE)
        deck.text(page, x + 250, y0 + 180, w - 500, 550, value, 10, GOLD if value != headers[0] else WHITE, bold=True, valign="center")
        x += w
    for idx, row in enumerate(rows):
        y = y0 + 1000 + idx * 1600
        fill = IVORY if idx % 2 == 0 else WHITE
        x = x0
        for col, (w, value) in enumerate(zip(widths, row)):
            deck.rect(page, x, y, w, 1600, fill, line=GOLD_LIGHT)
            deck.text(page, x + 280, y + 260, w - 560, 1050, value, 9.8,
                      INK if col != 2 else 0x275B34, bold=(col == 0 or col == 2), valign="center")
            x += w
    deck.text(page, 1600, H - 750, 29000, 350,
              "La propuesta puede convivir temporalmente con el sitio actual durante un piloto.", 8.5, MUTED, italic=True)

    # 6 — Journey
    page = deck.slide(IVORY)
    deck.title(page, "Experiencia", "Un recorrido continuo: descubrir, aprender, conectar, participar")
    journey = [
        ("1", "DESCUBRIR", "Identidad, bienvenida, horarios y eventos", DEMO / "inicio.png", GOLD),
        ("2", "APRENDER", "Doctrina por niveles, lecciones y referencias", DOCTRINA / "la-salvacion.png", GREEN),
        ("3", "CONECTAR", "Encontrar una iglesia y conocer a su pastor", DEMO / "iglesia-lima.png", CYAN),
        ("4", "PARTICIPAR", "Registrarse, conversar y acceder a materiales", DEMO / "evento-comunidad.png", RED),
    ]
    for i, (num, head, body, img, color) in enumerate(journey):
        x = 1200 + i * 8150
        deck.image(page, img, x, 4800, 7200, 4300, fit="cover")
        deck.rect(page, x, 4800, 1200, 1200, color, line=color)
        deck.text(page, x, 4930, 1200, 650, num, 20, WHITE, bold=True, align="center", valign="center")
        deck.text(page, x + 250, 9500, 6700, 750, head, 14, color, bold=True, align="center")
        deck.text(page, x + 450, 10400, 6300, 1800, body, 10.5, MUTED, align="center")
        if i < 3:
            deck.text(page, x + 7300, 6650, 850, 700, "→", 25, GOLD, bold=True, align="center")
    deck.rect(page, 3200, 13600, 27400, 1800, BLACK, line=BLACK, radius=180)
    deck.text(page, 4000, 14000, 25800, 850,
              "Cada paso deja una siguiente acción clara; el visitante no queda en una página aislada.",
              14, WHITE, bold=True, align="center", valign="center")
    deck.drop_last_slide()

    # 7 — Doctrine
    page = deck.slide(BLACK, dark=True)
    deck.title(page, "Formación", "Doctrina que se puede recorrer y administrar", dark=True)
    if PROTOTYPE_SCREENSHOT.exists():
        deck.image(page, PROTOTYPE_SCREENSHOT, 1500, 5000, 19000, 8200, fit="contain")
    else:
        deck.image(page, DOCTRINA / "la-salvacion.png", 1500, 4500, 19000, 10700, fit="cover")
    bullets = [
        ("3 niveles", "Básica, intermedia y avanzada"),
        ("Contenido rico", "Texto, imágenes, videos y documentos"),
        ("Trazabilidad", "Autoría, revisiones y fecha de publicación"),
        ("Interacción", "Comentarios públicos moderables"),
        ("Visualización", "Gráficos bíblicos interactivos"),
    ]
    for i, (head, body) in enumerate(bullets):
        y = 4700 + i * 2200
        deck.text(page, 22100, y, 9500, 550, head.upper(), 12, GOLD, bold=True)
        deck.text(page, 22100, y + 650, 9500, 800, body, 10.5, WHITE)
    deck.text(page, 1500, H - 900, 29500, 350,
              "Captura del prototipo funcional. El contenido demo debe sustituirse por material aprobado.", 8.2, GOLD_LIGHT, italic=True)

    # 8 — Network
    page = deck.slide(IVORY)
    deck.title(page, "Red", "Una arquitectura común con expresión local")
    churches = [
        ("PERÚ · LIMA", DEMO / "iglesia-lima.png"),
        ("PERÚ · AREQUIPA", DEMO / "iglesia-arequipa.png"),
        ("ESPAÑA · MADRID", DEMO / "iglesia-madrid.png"),
    ]
    for i, (label, img) in enumerate(churches):
        x = 1400 + i * 10600
        deck.image(page, img, x, 4500, 9600, 6000, fit="cover")
        deck.rect(page, x, 9300, 9600, 1200, BLACK, transparency=8)
        deck.text(page, x + 450, 9580, 8700, 520, label, 12, GOLD_LIGHT, bold=True, align="center")
    features = [
        "Página pública con ubicación, horarios y contacto",
        "Perfil del pastor y responsables de edición",
        "Eventos, predicaciones y materiales propios",
    ]
    for i, item in enumerate(features):
        x = 1500 + i * 10600
        deck.rect(page, x, 11700, 9300, 2700, WHITE, line=GOLD_LIGHT, radius=160)
        deck.text(page, x + 500, 12150, 8300, 1700, item, 11, INK, bold=True, align="center", valign="center")
    deck.text(page, 2500, 15700, 28800, 650,
              "Gobierno central de estructura y estándares · autonomía local sobre información autorizada", 13, MUTED, bold=True, align="center")
    deck.drop_last_slide()

    # 9 — Governance
    page = deck.slide(WHITE)
    deck.title(page, "Gobernanza", "Permisos que reflejan la estructura ministerial")
    roles = [
        ("APÓSTOL", "Gobierno, supervisión y publicación transversal", DEMO / "apostol.png", GOLD, 1),
        ("PASTOR DE PASTORES", "Acompaña y supervisa equipos pastorales", DEMO / "supervisor.png", CYAN, 2),
        ("PASTOR LOCAL", "Administra su iglesia y su contenido", DEMO / "pastor-lima.png", GREEN, 3),
        ("MIEMBRO / VISITANTE", "Participa según su perfil y permisos", DEMO / "miembro.png", RED, 4),
    ]
    for i, (role, body, img, color, level) in enumerate(roles):
        x = 1600 + i * 8000
        y = 5000 + i * 1000
        deck.image(page, img, x + 1900, y, 3600, 3600, fit="cover", focus=(0.5, 0.25))
        deck.rect(page, x + 1750, y + 3450, 3900, 650, color, line=color, radius=250)
        deck.text(page, x + 1850, y + 3520, 3700, 400, role, 8.5, WHITE, bold=True, align="center", valign="center")
        deck.text(page, x + 300, y + 4400, 6900, 1500, body, 10.5, MUTED, bold=True, align="center")
        if i < 3:
            deck.line(page, x + 7200, y + 1800, x + 8200, y + 2800, GOLD_LIGHT, 80)
    deck.rect(page, 3000, 15100, 27800, 1500, PALE_GOLD, line=GOLD_LIGHT, radius=160)
    deck.text(page, 3600, 15420, 26600, 700,
              "Principio: cada persona administra solo lo que le corresponde; los privilegios se auditan y revisan.",
              11.5, INK, bold=True, align="center", valign="center")

    # 10 — Ecosystem
    page = deck.slide(BLACK, dark=True)
    deck.title(page, "Ecosistema", "Contenido que circula entre formación y comunidad", dark=True)
    ecosystem = [
        ("EVENTOS", DEMO / "evento-jovenes.png", "Agenda local por iglesia"),
        ("MATERIALES", DEMO / "materiales.png", "Presentaciones y documentos"),
        ("FOROS", DEMO / "foros.png", "Conversación moderada"),
        ("PREDICACIÓN", DOCTRINA / "la-oracion.png", "Videos y recursos relacionados"),
    ]
    for i, (head, img, body) in enumerate(ecosystem):
        x = 1200 + i * 8100
        deck.image(page, img, x, 4700, 7300, 6200, fit="cover")
        deck.rect(page, x, 9300, 7300, 1600, BLACK, transparency=5)
        deck.text(page, x + 300, 9570, 6700, 450, head, 12, GOLD, bold=True, align="center")
        deck.text(page, x + 300, 10100, 6700, 450, body, 9.5, WHITE, align="center")
    deck.text(page, 2100, 12700, 29600, 2300,
              "Un sermón puede enlazar una lección; una iglesia puede publicar un evento; un miembro puede encontrar material; "
              "un foro puede sostener la conversación. La plataforma conecta esas piezas.",
              16, WHITE, bold=True, font=SERIF, align="center", valign="center")
    deck.drop_last_slide()

    # 11 — Stakeholders
    page = deck.slide(IVORY)
    deck.title(page, "Valor", "Beneficios concretos para cada audiencia")
    stakeholders = [
        ("LIDERAZGO", "Visión de la red, estándares comunes y control de permisos", GOLD),
        ("PASTORES", "Página local, publicación de recursos y vínculo con su comunidad", GREEN),
        ("MIEMBROS", "Formación, materiales, eventos y participación", CYAN),
        ("VISITANTES", "Ruta clara para conocer, aprender y encontrar una iglesia", RED),
        ("EQUIPO DIGITAL", "Modelos reutilizables, CMS y menor duplicación de contenido", 0x7B5EA7),
        ("RED INTERNACIONAL", "Directorio estructurado y crecimiento por países y ciudades", 0x3F6D78),
    ]
    for i, (head, body, color) in enumerate(stakeholders):
        x = 1600 + (i % 2) * 15700
        y = 4500 + (i // 2) * 3900
        deck.rect(page, x, y, 14500, 3000, WHITE, line=GOLD_LIGHT, radius=180)
        deck.rect(page, x, y, 1700, 3000, color, line=color)
        deck.text(page, x + 300, y + 930, 1100, 800, str(i + 1).zfill(2), 18, WHITE, bold=True, align="center")
        deck.text(page, x + 2300, y + 450, 11000, 600, head, 13, color, bold=True)
        deck.text(page, x + 2300, y + 1250, 11000, 1100, body, 10.5, MUTED)

    # 12 — Roadmap
    page = deck.slide(WHITE)
    deck.title(page, "Implementación", "Un piloto controlado en cuatro etapas")
    phases = [
        ("1", "VALIDAR", "2 semanas", "Contenido, roles, vocabulario y alcance del piloto", GOLD),
        ("2", "PREPARAR", "2–3 semanas", "Hosting, dominio, seguridad, respaldos y analítica", CYAN),
        ("3", "PILOTEAR", "4 semanas", "Los Ángeles + 2 iglesias de cobertura", GREEN),
        ("4", "DECIDIR", "1 semana", "Medir, corregir y aprobar expansión gradual", RED),
    ]
    deck.line(page, 3400, 8100, 30400, 8100, GOLD_LIGHT, 140)
    for i, (num, head, duration, body, color) in enumerate(phases):
        x = 2000 + i * 7900
        deck.rect(page, x + 2200, 6900, 1500, 1500, color, line=color, radius=700)
        deck.text(page, x + 2200, 7150, 1500, 700, num, 18, WHITE, bold=True, align="center", valign="center")
        deck.text(page, x, 9200, 5900, 650, head, 14, color, bold=True, align="center")
        deck.pill(page, x + 1450, 10050, 3000, duration, WHITE, BLACK)
        deck.text(page, x + 250, 11200, 5400, 2100, body, 10.5, MUTED, align="center")
    deck.rect(page, 2200, 14800, 29400, 1300, PALE_GREEN, line=0xBAD5A4, radius=160)
    deck.text(page, 2800, 15100, 28200, 650,
              "El sitio vigente puede mantenerse activo durante todo el piloto; no se requiere una migración inmediata.",
              11, 0x275B34, bold=True, align="center", valign="center")

    # 13 — Safeguards and metrics
    page = deck.slide(IVORY)
    deck.title(page, "Antes de producción", "Controles y métricas para una decisión responsable")
    controls = [
        ("SEGURIDAD", "Revisión de acceso, secretos, formularios, sesiones y dependencias"),
        ("CONTENIDO", "Aprobación doctrinal, estilo editorial y responsables por sección"),
        ("OPERACIÓN", "Hosting, dominio, respaldos, recuperación y monitoreo"),
        ("PRIVACIDAD", "Política de datos, consentimiento y tratamiento de perfiles"),
    ]
    for i, (head, body) in enumerate(controls):
        x = 1500 + (i % 2) * 16000
        y = 4400 + (i // 2) * 3700
        deck.card(page, x, y, 14600, 3000, head, body, accent=RED if i in (0, 3) else GOLD)
    deck.text(page, 1600, 12500, 9000, 600, "MÉTRICAS DEL PILOTO", 13, GOLD, bold=True)
    metrics = [
        "Contenido aprobado y publicado",
        "Actualización por responsables locales",
        "Búsquedas y rutas completadas",
        "Registro y participación",
        "Incidencias y tiempo de resolución",
    ]
    for i, item in enumerate(metrics):
        x = 1600 + i * 6200
        deck.rect(page, x, 13600, 5600, 1900, WHITE, line=GOLD_LIGHT, radius=160)
        deck.text(page, x + 300, 14000, 5000, 1000, item, 9.5, INK, bold=True, align="center", valign="center")
    deck.text(page, 1600, H - 750, 29000, 350,
              "No se proyectan porcentajes de mejora antes de contar con una línea base y datos del piloto.", 8.5, MUTED, italic=True)

    # 14 — Ask
    page = deck.slide(BLACK, dark=True)
    deck.image(page, DEMO / "evento-comunidad.png", 17000, 0, W - 17000, H, fit="cover", focus=(0.55, 0.5))
    deck.rect(page, 15700, 0, W - 15700, H, BLACK, transparency=35)
    deck.image(page, LOGO, 1600, 1200, 2600, 1200, fit="contain")
    deck.text(page, 1600, 4000, 13700, 2300, "DECISIÓN SOLICITADA", 27, GOLD, bold=True, font=SERIF)
    asks = [
        "Aprobar un piloto sin reemplazar todavía el sitio vigente",
        "Nombrar un responsable pastoral y uno técnico",
        "Seleccionar Los Ángeles y dos iglesias participantes",
        "Validar contenido, permisos y criterios de éxito",
    ]
    for i, item in enumerate(asks):
        y = 7200 + i * 2000
        deck.rect(page, 1700, y, 900, 900, GOLD, line=GOLD, radius=400)
        deck.text(page, 1700, y + 100, 900, 500, str(i + 1), 13, BLACK, bold=True, align="center", valign="center")
        deck.text(page, 3000, y - 50, 12000, 1050, item, 12, WHITE, bold=True, valign="center")
    deck.text(page, 18000, 14300, 13700, 1900,
              "La tecnología es el medio.\nEl objetivo es formar, conectar y servir mejor.",
              18, WHITE, bold=True, font=SERIF, align="center")

    # 15 — Sources
    page = deck.slide(WHITE)
    deck.title(page, "Fuentes", "Base de la comparación y alcance de la propuesta")
    sources = [
        ("Sitio actual — portada", "https://www.ministerioselimlosangeles.net/"),
        ("Quiénes somos", "https://www.ministerioselimlosangeles.net/quienes-somos"),
        ("Predicaciones", "https://www.ministerioselimlosangeles.net/predicas"),
        ("Iglesias bajo cobertura", "https://www.ministerioselimlosangeles.net/iglesias-bajo-cobertura"),
        ("Contacto y horarios", "https://www.ministerioselimlosangeles.net/contact-us"),
        ("Prototipo", "Repositorio local ministerios-elim, revisión funcional del 14/10/2026"),
    ]
    for i, (head, url) in enumerate(sources):
        y = 4500 + i * 1750
        deck.text(page, 1800, y, 8000, 500, head.upper(), 10, GOLD if i < 5 else GREEN, bold=True)
        deck.text(page, 10200, y, 21000, 650, url, 10, INK)
        deck.line(page, 1800, y + 950, 31200, y + 950, GOLD_LIGHT, 25)
    deck.rect(page, 1800, 15700, 29400, 1500, PALE_GOLD, line=GOLD_LIGHT, radius=160)
    deck.text(page, 2400, 16020, 28200, 750,
              "Revisión pública puntual. Las funciones privadas del sitio actual no se evaluaron. El prototipo usa datos e imágenes demo.",
              9.5, MUTED, bold=True, align="center", valign="center")


def create_pptx(pages, commands, target: Path):
    """Create a widescreen PPTX with editable text, shapes and independent images."""
    ns = "http://schemas.openxmlformats.org/package/2006/relationships"
    content_types = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">',
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>',
        '<Default Extension="xml" ContentType="application/xml"/>',
        '<Default Extension="png" ContentType="image/png"/>',
        '<Default Extension="jpg" ContentType="image/jpeg"/>',
        '<Default Extension="jpeg" ContentType="image/jpeg"/>',
        '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>',
        '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>',
        '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>',
        '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>',
        '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>',
        '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>',
    ]
    for i in range(1, len(pages) + 1):
        content_types.append(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>')
    content_types.append('</Types>')

    slide_ids = "".join(f'<p:sldId id="{255+i}" r:id="rId{i}"/>' for i in range(1, len(pages) + 1))
    presentation = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId{len(pages)+1}"/></p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx="12192000" cy="6858000" type="screen16x9"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>'''
    presentation_rels = [f'''<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>''' for i in range(1, len(pages) + 1)]
    presentation_rels.append(f'''<Relationship Id="rId{len(pages)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>''')
    root_rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'''
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><dc:title>Ministerios Elim — Propuesta de plataforma digital</dc:title><dc:subject>Presentación para el liderazgo</dc:subject><dc:creator>Ministerios Elim</dc:creator><cp:lastModifiedBy>Ministerios Elim</cp:lastModifiedBy><dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>'''
    app = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><Application>Ministerios Elim</Application><PresentationFormat>Widescreen</PresentationFormat><Slides>{len(pages)}</Slides><Notes>0</Notes><HiddenSlides>0</HiddenSlides><Company>Ministerios Elim</Company><AppVersion>1.0</AppVersion></Properties>'''
    group = '''<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'''
    master = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree>{group}</p:spTree></p:cSld><p:clrMap accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" bg1="lt1" bg2="lt2" folHlink="folHlink" hlink="hlink" tx1="dk1" tx2="dk2"/><p:sldLayoutIdLst><p:sldLayoutId id="1" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>'''
    layout = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="En blanco"><p:spTree>{group}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>'''
    theme = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Ministerios Elim"><a:themeElements><a:clrScheme name="Elim"><a:dk1><a:srgbClr val="111111"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="242424"/></a:dk2><a:lt2><a:srgbClr val="F7F3EA"/></a:lt2><a:accent1><a:srgbClr val="C5A059"/></a:accent1><a:accent2><a:srgbClr val="87C45B"/></a:accent2><a:accent3><a:srgbClr val="36BBD3"/></a:accent3><a:accent4><a:srgbClr val="A94A43"/></a:accent4><a:accent5><a:srgbClr val="7B5EA7"/></a:accent5><a:accent6><a:srgbClr val="3F6D78"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Elim"><a:majorFont><a:latin typeface="Liberation Serif"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Liberation Sans"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme><a:fmtScheme name="Elim"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>'''

    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", "".join(content_types))
        archive.writestr("_rels/.rels", root_rels)
        archive.writestr("ppt/presentation.xml", presentation)
        archive.writestr("ppt/_rels/presentation.xml.rels", f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}">{''.join(presentation_rels)}</Relationships>''')
        archive.writestr("docProps/core.xml", core)
        archive.writestr("docProps/app.xml", app)
        archive.writestr("ppt/slideMasters/slideMaster1.xml", master)
        archive.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>''')
        archive.writestr("ppt/slideLayouts/slideLayout1.xml", layout)
        archive.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>''')
        archive.writestr("ppt/theme/theme1.xml", theme)
        media_map = {}
        media_counter = 0

        def color_hex(value):
            return f"{value:06X}"

        def emu_x(value):
            return round(value * 12192000 / W)

        def emu_y(value):
            return round(value * 6858000 / H)

        def transform(x, y, w, h):
            return f'<a:xfrm><a:off x="{emu_x(x)}" y="{emu_y(y)}"/><a:ext cx="{emu_x(w)}" cy="{emu_y(h)}"/></a:xfrm>'

        def shape_xml(command, shape_id):
            kind = command["type"]
            name = f"Objeto editable {shape_id}"
            if kind == "rect":
                opacity = max(0, min(100000, round((100 - command["transparency"]) * 1000)))
                geometry = "roundRect" if command.get("radius") else "rect"
                return f'''<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>{transform(command['x'], command['y'], command['w'], command['h'])}<a:prstGeom prst="{geometry}"><a:avLst/></a:prstGeom><a:solidFill><a:srgbClr val="{color_hex(command['fill'])}"><a:alpha val="{opacity}"/></a:srgbClr></a:solidFill><a:ln w="6350"><a:solidFill><a:srgbClr val="{color_hex(command['line'])}"/></a:solidFill></a:ln></p:spPr></p:sp>'''
            if kind == "line":
                x, y = min(command["x1"], command["x2"]), min(command["y1"], command["y2"])
                w, h = abs(command["x2"] - command["x1"]), abs(command["y2"] - command["y1"])
                return f'''<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr>{transform(x, y, max(w, 1), max(h, 1))}<a:prstGeom prst="line"><a:avLst/></a:prstGeom><a:noFill/><a:ln w="{max(6350, emu_x(command['width']))}"><a:solidFill><a:srgbClr val="{color_hex(command['color'])}"/></a:solidFill></a:ln></p:spPr></p:sp>'''
            if kind == "text":
                align = {"left": "l", "center": "ctr", "right": "r"}[command["align"]]
                anchor = {"top": "t", "center": "ctr", "bottom": "b"}[command["valign"]]
                margin_x, margin_y = emu_x(command["margin"]), emu_y(command["margin"])
                bold = ' b="1"' if command["bold"] else ""
                italic = ' i="1"' if command["italic"] else ""
                font_size = max(100, round(command["size"] * 100))
                paragraphs = []
                for paragraph in command["value"].split("\n"):
                    value = escape(paragraph)
                    paragraphs.append(f'''<a:p><a:pPr algn="{align}"/><a:r><a:rPr lang="es-PE" sz="{font_size}"{bold}{italic}><a:solidFill><a:srgbClr val="{color_hex(command['color'])}"/></a:solidFill><a:latin typeface="{escape(command['font'])}"/></a:rPr><a:t>{value}</a:t></a:r><a:endParaRPr lang="es-PE" sz="{font_size}"/></a:p>''')
                return f'''<p:sp><p:nvSpPr><p:cNvPr id="{shape_id}" name="{name}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr><p:spPr>{transform(command['x'], command['y'], command['w'], command['h'])}<a:noFill/><a:ln><a:noFill/></a:ln></p:spPr><p:txBody><a:bodyPr wrap="square" anchor="{anchor}" lIns="{margin_x}" rIns="{margin_x}" tIns="{margin_y}" bIns="{margin_y}"/><a:lstStyle/>{''.join(paragraphs)}</p:txBody></p:sp>'''
            raise ValueError(f"Tipo de objeto no soportado: {kind}")

        for i, slide_commands in enumerate(commands, 1):
            shapes = []
            slide_relationships = [f'''<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>''']
            shape_id = 2
            relationship_id = 2
            for command in slide_commands:
                if command["type"] != "image":
                    shapes.append(shape_xml(command, shape_id))
                    shape_id += 1
                    continue
                source = Path(command["source"]).resolve()
                source_key = str(source)
                if source_key not in media_map:
                    media_counter += 1
                    suffix = source.suffix.lower().lstrip(".") or "png"
                    if suffix == "jpeg":
                        suffix = "jpg"
                    media_name = f"image{media_counter}.{suffix}"
                    media_map[source_key] = media_name
                    archive.write(source, f"ppt/media/{media_name}")
                media_name = media_map[source_key]
                rid = f"rId{relationship_id}"
                relationship_id += 1
                slide_relationships.append(f'''<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{media_name}"/>''')
                shapes.append(f'''<p:pic><p:nvPicPr><p:cNvPr id="{shape_id}" name="Imagen {shape_id}"/><p:cNvPicPr><a:picLocks noChangeAspect="1"/></p:cNvPicPr><p:nvPr/></p:nvPicPr><p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill><p:spPr>{transform(command['x'], command['y'], command['w'], command['h'])}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr></p:pic>''')
                shape_id += 1
            slide = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree>{group}{''.join(shapes)}</p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>'''
            rels = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="{ns}">{''.join(slide_relationships)}</Relationships>'''
            archive.writestr(f"ppt/slides/slide{i}.xml", slide)
            archive.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    deck = Deck()
    build_deck(deck)
    pptx = OUTPUT_DIR / "Ministerios_Elim_Propuesta_Liderazgo.pptx"
    pdf = OUTPUT_DIR / "Ministerios_Elim_Propuesta_Liderazgo.pdf"
    create_pptx(deck.pages, deck.commands, pptx)
    deck.pages[0].save(pdf, "PDF", resolution=120, save_all=True, append_images=deck.pages[1:])
    print(pptx)
    print(pdf)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error creando la presentación: {exc}", file=sys.stderr)
        raise
