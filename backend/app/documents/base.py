import textwrap
from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

FONT_DIR = Path(__file__).parent / "fonts"
pdfmetrics.registerFont(TTFont("Urdu", str(FONT_DIR / "NotoNaskhArabic-Regular.ttf")))
pdfmetrics.registerFont(TTFont("Latin", str(FONT_DIR / "NotoSans-Regular.ttf")))


class Document:
    def __init__(self, title, settings, thermal=False):
        self.output = BytesIO()
        self.width, self.height = (226, 842) if thermal else A4
        self.margin = 14 if thermal else 42
        self.y = self.height - 38
        self.canvas = canvas.Canvas(self.output, pagesize=(self.width, self.height))
        self.canvas.setTitle(title)
        if settings.logo:
            self.canvas.drawImage(
                ImageReader(BytesIO(settings.logo)),
                self.margin,
                self.height - 78,
                width=40,
                height=40,
                preserveAspectRatio=True,
                mask="auto",
            )
        if settings.name_ur:
            self.line(settings.name_ur, 18)
        self.line(settings.name, 12 if settings.name_ur else 18)
        if settings.address_ur:
            self.line(settings.address_ur, 10)
        self.line(settings.address, 10)
        self.line(settings.phone, 10)
        self.line(title, 14)
        self.y -= 8
        self.canvas.setStrokeColorRGB(0.15, 0.4, 0.3)
        self.canvas.line(self.margin, self.y, self.width - self.margin, self.y)
        self.y -= 24

    def line(self, value, size=12):
        for paragraph in str(value).splitlines() or [""]:
            for chunk in textwrap.wrap(
                paragraph, width=28 if self.width < 300 else 78
            ) or [""]:
                if self.y < 45:
                    self.canvas.showPage()
                    self.y = self.height - 40
                visual = get_display(arabic_reshaper.reshape(chunk), base_dir="R")
                runs = []
                for char in visual:
                    font = "Latin" if ord(char) < 0x600 else "Urdu"
                    if runs and runs[-1][0] == font:
                        runs[-1] = (font, runs[-1][1] + char)
                    else:
                        runs.append((font, char))
                x = (
                    self.width
                    - self.margin
                    - sum(
                        pdfmetrics.stringWidth(segment, font, size)
                        for font, segment in runs
                    )
                )
                for font, segment in runs:
                    self.canvas.setFont(font, size)
                    self.canvas.drawString(x, self.y, segment)
                    x += pdfmetrics.stringWidth(segment, font, size)
                self.y -= size * 1.8

    def finish(self):
        self.canvas.save()
        return self.output.getvalue()
