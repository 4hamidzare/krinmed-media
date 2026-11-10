"""Krinmed reel: Bowie & Dick Test Pack breaking out of an Instagram post frame.
Usage: python3 reel.py frames t1 t2 ...   (writes preview PNGs)
       python3 reel.py render              (encodes reel.mp4)"""
import sys, math, subprocess, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 12.0
A = "assets/"
RED, GREEN, LIME, MAROON = (231, 52, 50), (141, 191, 34), (195, 210, 1), (118, 17, 20)
BG = (13, 15, 18)

def f(fam, w, s): return ImageFont.truetype(f"ttf/{fam}-{w}.ttf", s)
FA = lambda w, s: f("vazirmatn", w, s)
EN = lambda w, s: f("inter", w, s)
IOTF = {400:"Regular",600:"SemiBold",800:"ExtraBold"}
RU = lambda w, s: ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{IOTF[w]}.otf", s)

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3
def ease_io(x): x = max(0, min(1, x)); return x * x * (3 - 2 * x)
def seg(t, a, b): return ease((t - a) / (b - a))

photo = Image.open(A + "bowie-dick-test-pack-dark-02.png").convert("RGB")
pw, ph = photo.size
photo_sq = photo.crop(((pw - ph) // 2, 0, (pw - ph) // 2 + ph, ph)).resize((900, 900), Image.LANCZOS)
cut = Image.open(A + "pack-cutout.png")
klogo = Image.open(A + "krinmed-logo.png"); eep = Image.open(A + "eep-logo.png")

def fit(im, w): return im.resize((w, round(im.size[1] * w / im.size[0])), Image.LANCZOS)
klogo_s = fit(klogo, 120); klogo_end = fit(klogo, 520); eep_end = fit(eep, 300)

# cutout placement inside the post photo (square crop offset)
crop_x0 = (pw - ph) // 2
CX0, CY0 = 152 - crop_x0, 129          # cutout bbox origin in source photo
SC = 900 / ph
cutc = cut.crop((crop_x0 - 152, 0, cut.size[0], cut.size[1])); CUTC_X = 0

def text(d, xy, s, font, fill, anchor="la", **kw):
    d.text(xy, s, font=font, fill=fill, anchor=anchor, **kw)

def card(alpha):
    """Instagram-like post card (without photo) as RGBA 960x1300."""
    c = Image.new("RGBA", (960, 1290), (0, 0, 0, 0))
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, 959, 1289), 36, fill=(24, 26, 31, 255))
    av = Image.new("RGBA", (96, 96), (0, 0, 0, 0)); ImageDraw.Draw(av).ellipse((0, 0, 95, 95), fill=(0, 0, 0, 255))
    av.alpha_composite(fit(klogo, 84), (6, 30))
    ring = ImageDraw.Draw(c); ring.ellipse((26, 26, 130, 130), outline=RED, width=5)
    c.alpha_composite(av, (30, 30))
    text(d, (150, 78), "krin.med", EN(800, 38), (255, 255, 255), "lm")
    text(d, (150, 116), "Krinmed Inc.", EN(400, 26), (150, 150, 155), "lm")
    text(d, (910, 70), "•••", EN(800, 30), (255, 255, 255), "rm")
    y = 1080
    # heart, comment, share (simple strokes)
    d.ellipse((30, y, 62, y + 30), outline="white", width=5); d.ellipse((52, y, 84, y + 30), outline="white", width=5)
    d.polygon([(32, y + 20), (57, y + 52), (82, y + 20)], fill=(24, 26, 31, 255)); d.line([(34, y + 22), (57, y + 50), (80, y + 22)], fill="white", width=5)
    d.ellipse((120, y, 168, y + 46), outline="white", width=5)
    d.polygon([(205, y + 4), (255, y + 4), (222, y + 50)], outline="white", width=5)
    d.rectangle((890, y, 920, y + 44), outline="white", width=5)
    text(d, (30, 1170), "krin.med", EN(800, 32), (255, 255, 255), "lm")
    text(d, (930, 1170), "تست روزانه‌ی اتوکلاو پیش‌خلأ", FA(600, 32), (220, 220, 225), "rm", direction="rtl")
    text(d, (30, 1230), "View all comments", EN(400, 26), (130, 130, 135), "lm")
    if alpha < 1: c.putalpha(c.getchannel("A").point(lambda v: int(v * alpha)))
    return c

CARD = card(1)
CARD_X, CARD_Y = 60, 360           # card position on canvas
PH_X, PH_Y = CARD_X + 30, CARD_Y + 160  # photo area top-left (900x900)

def shadow(im, r=28, op=150):
    a = im.getchannel("A").filter(ImageFilter.GaussianBlur(r)).point(lambda v: v * op // 255)
    s = Image.new("RGBA", im.size, (0, 0, 0, 0)); s.putalpha(a); return s

LINES = [
    ("fa", "تست بووی‌دیک؛ هر روز", FA(800, 70), RED),
    ("fa", "در اتوکلاو پیش‌خلأِ خالی", FA(800, 70), RED),
    ("en", "Bowie-Dick test: daily, in an", EN(600, 40), (235, 235, 235)),
    ("en", "empty prevacuum sterilizer", EN(600, 40), (235, 235, 235)),
    ("ar", "اختبار بووي ديك يومياً في جهاز", FA(600, 40), (235, 235, 235)),
    ("ar", "تعقيم بالتفريغ المسبق وهو فارغ", FA(600, 40), (235, 235, 235)),
    ("ru", "Тест Бови–Дика: ежедневно,", RU(600, 40), (235, 235, 235)),
    ("ru", "в пустом форвакуумном стерилизаторе", RU(600, 38), (235, 235, 235)),
]

def frame(t):
    img = Image.new("RGBA", (W, H), BG + (255,))
    d = ImageDraw.Draw(img)
    # subtle side brand bars
    d.rectangle((0, 0, 14, H), fill=GREEN); d.rectangle((0, 0, 14, 300), fill=RED)

    # ---------- scene 1: post card + break-out (0 - 5.2s) ----------
    cin = seg(t, 0.0, 0.7); cout = seg(t, 4.4, 5.2)
    if t < 5.3:
        cy = CARD_Y + int(80 * (1 - cin)) + int(500 * ease_io((t - 4.4) / 0.8) if t > 4.4 else 0)
        ca = cin * (1 - cout)
        c = CARD if ca >= 1 else card(ca)
        img.alpha_composite(c, (CARD_X, cy))
        # photo with background, clipped to frame
        p = seg(t, 1.2, 2.6)  # break-out progress
        ph = photo_sq.copy().convert("RGBA")
        if p > 0:  # stage darkens as the pack leaves it
            ph = Image.blend(ph, Image.new("RGBA", ph.size, (8, 9, 11, 255)), 0.85 * p)
        if ca < 1: ph.putalpha(int(255 * ca))
        img.alpha_composite(ph, (PH_X, cy + 160))
        # break-out: cutout lifts out of the photo and overflows above the frame
        if t >= 1.0:
            # start: exactly where the boxes sit in the photo; end: centred, larger, above frame top
            x0, y0, w0 = PH_X + CUTC_X * SC, cy + 160 + CY0 * SC, cutc.size[0] * SC
            w1 = 1000; x1 = PH_X + (900 - w1) / 2; h1 = cutc.size[1] * w1 / cutc.size[0]
            y1 = cy + 160 + 560 - h1
            cw = round(w0 + (w1 - w0) * p); ch = round(cutc.size[1] * cw / cutc.size[0])
            x = x0 + (x1 - x0) * p; y = y0 + (y1 - y0) * p
            co = cutc.resize((cw, ch), Image.LANCZOS)
            if ca < 1: co.putalpha(co.getchannel("A").point(lambda v: int(v * ca)))
            if p > 0:
                sh = shadow(co, 30, int(170 * p)); img.alpha_composite(sh, (int(x) + 10, int(y) + 40))
            img.alpha_composite(co, (int(x), int(y)))
        # title above card
        ta = seg(t, 2.2, 2.9) * (1 - cout)
        if ta > 0:
            lay = Image.new("RGBA", (W, 200), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            text(ld, (W // 2, 70), "Bowie & Dick Test Pack", EN(800, 56), (255, 255, 255), "mm")
            text(ld, (W // 2, 140), "For use in pre-vacuum sterilizers", EN(400, 32), (170, 170, 175), "mm")
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * ta)))
            img.alpha_composite(lay, (0, 110 - int(30 * (1 - ta))))

    # ---------- scene 2: four-language message (4.9 - 9.2s) ----------
    if 4.9 <= t < 9.4:
        out = seg(t, 8.6, 9.3)
        y = 470
        for i, (lang, s, fnt, col) in enumerate(LINES):
            a = seg(t, 5.0 + 0.18 * i, 5.6 + 0.18 * i) * (1 - out)
            if a <= 0: y += 0;
            lay = Image.new("RGBA", (W, 130), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
            if lang in ("fa", "ar"):
                text(ld, (W - 90, 65), s, fnt, col, "rm", direction="rtl")
            else:
                text(ld, (90, 65), s, fnt, col, "lm")
            lay.putalpha(lay.getchannel("A").point(lambda v, a=a: int(v * a)))
            dx = int(60 * (1 - a)) * (-1 if lang in ("fa", "ar") else 1)
            img.alpha_composite(lay, (dx, y))
            y += 112 if lang == "fa" else 70
            if i in (1, 3, 5): y += 50
        sa = seg(t, 6.6, 7.2) * (1 - out)
        lay = Image.new("RGBA", (W, 80), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        ld.line([(90, 10), (990, 10)], fill=LIME, width=3)
        text(ld, (90, 50), "Source: CDC · Sterilizing Practices", EN(400, 28), (150, 150, 155), "lm")
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * sa)))
        img.alpha_composite(lay, (0, 1560))
        # small pack thumbnail at top
        ta = seg(t, 5.0, 5.6) * (1 - out)
        th = fit(cut, 460); th.putalpha(th.getchannel("A").point(lambda v: int(v * ta)))
        img.alpha_composite(th, ((W - th.size[0]) // 2, 140))

    # ---------- scene 3: end card (9.1 - 12s) ----------
    if t >= 9.1:
        a = seg(t, 9.1, 9.8)
        lay = Image.new("RGBA", (W, H), (255, 255, 255, 255)); ld = ImageDraw.Draw(lay)
        ld.rectangle((0, 0, 14, H), fill=GREEN); ld.rectangle((0, 0, 14, 300), fill=RED)
        lay.alpha_composite(klogo_end, ((W - klogo_end.size[0]) // 2, 360))
        th = fit(cut, 820)
        lay.alpha_composite(shadow(th, 30, 90), ((W - th.size[0]) // 2 + 8, 760 + 30))
        lay.alpha_composite(th, ((W - th.size[0]) // 2, 760))
        text(ld, (W // 2, 1390), "Bowie & Dick Test Pack", EN(800, 54), (30, 30, 30), "mm")
        lay.alpha_composite(eep_end, ((W - eep_end.size[0]) // 2, 1450))
        ld.line([(90, 1720), (990, 1720)], fill=LIME, width=3)
        text(ld, (90, 1775), "info@krinmed.com", EN(600, 34), (110, 110, 110), "lm")
        text(ld, (990, 1775), "krinmed.com", EN(800, 36), GREEN, "rm")
        lay.putalpha(int(255 * a))
        img.alpha_composite(lay)
    return img.convert("RGB")

if __name__ == "__main__":
    if sys.argv[1] == "frames":
        for ts in sys.argv[2:]:
            frame(float(ts)).save(f"prev-{ts}.png")
    else:
        tmp = "reel.tmp.mp4"
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                              "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "18",
                              "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp],
                             stdin=subprocess.PIPE)
        for i in range(int(DUR * FPS)):
            p.stdin.write(frame(i / FPS).tobytes())
        p.stdin.close()
        if p.wait() == 0: os.replace(tmp, "reel.mp4"); print("ok")
