import math, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

TG = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-"
INTER = "/usr/share/fonts/opentype/inter/Inter-"
RED = (227, 10, 23)
WHITE = (245, 242, 236)
GREY = (160, 156, 150)
BG = (10, 10, 11)

def F(kind, size):
    m = {"serif": TG + "regular.otf", "serif-i": TG + "italic.otf",
         "serif-b": TG + "bold.otf", "serif-bi": TG + "bolditalic.otf",
         "sans": INTER + "Regular.otf", "sans-l": INTER + "Light.otf",
         "sans-m": INTER + "Medium.otf", "sans-sb": INTER + "SemiBold.otf"}
    return ImageFont.truetype(m[kind], size)

def text_img(s, font, fill=WHITE, tracking=0, maxw=None):
    """Render text to a tight RGBA image, optional letter-spacing; shrink to maxw."""
    if maxw:
        while True:
            w = _measure(s, font, tracking)
            if w <= maxw: break
            font = ImageFont.truetype(font.path, font.size - 2)
    w = _measure(s, font, tracking)
    asc, desc = font.getmetrics()
    h = asc + desc
    im = Image.new("RGBA", (int(w) + 20, h + 20), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 10
    if tracking == 0:
        d.text((x, 10), s, font=font, fill=fill)
    else:
        for ch in s:
            d.text((x, 10), ch, font=font, fill=fill)
            x += font.getlength(ch) + tracking
    return im

def _measure(s, font, tracking):
    if tracking == 0: return font.getlength(s)
    return sum(font.getlength(c) for c in s) + tracking * (len(s) - 1)

def place(base, im, cx, cy, alpha=1.0):
    if alpha <= 0.003: return
    if alpha < 1:
        im = im.copy()
        a = im.getchannel("A").point(lambda v: int(v * alpha))
        im.putalpha(a)
    base.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))

def background(w, h):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    cx, cy = w / 2, h * 0.45
    r = np.sqrt(((x - cx) / w) ** 2 + ((y - cy) / h) ** 2)
    v = np.clip(1 - r * 1.35, 0, 1) ** 1.6
    base = np.array(BG, np.float32)
    glow = np.array([30, 22, 20], np.float32)
    img = base[None, None] + glow[None, None] * v[..., None]
    return Image.fromarray(img.clip(0, 255).astype(np.uint8)).convert("RGBA")

def grain(w, h, seed, amt=7):
    rng = np.random.default_rng(seed)
    n = rng.normal(0, amt, (h, w)).astype(np.float32)
    return n

def apply_grain(img, n):
    a = np.asarray(img.convert("RGB")).astype(np.float32) + n[..., None]
    return Image.fromarray(a.clip(0, 255).astype(np.uint8)).convert("RGBA")

def logo_white(width):
    src = Image.open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"logo_src.png")).convert("RGBA")
    a = np.asarray(src).astype(np.float32)
    lum = a[..., :3].mean(-1)
    alpha = (255 - lum) / 255 * a[..., 3]
    out = np.zeros_like(a)
    out[..., :3] = WHITE
    out[..., 3] = alpha
    im = Image.fromarray(out.clip(0, 255).astype(np.uint8))
    bbox = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    im = im.crop(bbox)
    h = int(im.height * width / im.width)
    return im.resize((width, h), Image.LANCZOS)

# ---------- Turkish flag (official geometry, Wikimedia SVG units 1200x800) ----------
def flag_flat(W):
    S = 3
    w, h = W * S, int(W * S * 2 / 3)
    k = w / 1200
    im = Image.new("RGBA", (w, h), RED + (255,))
    d = ImageDraw.Draw(im)
    def circ(cx, cy, r, col):
        d.ellipse([(cx - r) * k, (cy - r) * k, (cx + r) * k, (cy + r) * k], fill=col)
    circ(425, 400, 200, (255, 255, 255))
    circ(475, 400, 160, RED)
    cx, cy, R = 683.334, 400, 100
    ri = R * 0.381966
    pts = []
    for i in range(10):
        ang = math.pi + i * math.pi / 5
        rr = R if i % 2 == 0 else ri
        pts.append(((cx + rr * math.cos(ang)) * k, (cy + rr * math.sin(ang)) * k))
    d.polygon(pts, fill=(255, 255, 255))
    return im.resize((W, int(W * 2 / 3)), Image.LANCZOS)

def flag_wave(flat, t, amp=0.035, waves=1.6, speed=1.3):
    W, H = flat.size
    pad = int(H * amp * 2.2) + 4
    src = np.asarray(flat).astype(np.float32)
    out = np.zeros((H + 2 * pad, W, 4), np.float32)
    xs = np.arange(W)
    u = xs / W
    phase = 2 * math.pi * (u * waves) - t * speed * 2 * math.pi
    dy = amp * H * np.sin(phase) * (0.25 + u)
    shade = 1 + 0.16 * np.cos(phase) * (0.3 + u)
    ys = np.arange(H + 2 * pad)[:, None] - pad - dy[None, :]
    y0 = np.floor(ys).astype(int); fr = ys - y0
    valid0 = (y0 >= 0) & (y0 < H); valid1 = (y0 + 1 >= 0) & (y0 + 1 < H)
    c0 = np.clip(y0, 0, H - 1); c1 = np.clip(y0 + 1, 0, H - 1)
    X = np.broadcast_to(xs[None, :], ys.shape)
    p0 = src[c0, X] * valid0[..., None]
    p1 = src[c1, X] * valid1[..., None]
    pix = p0 * (1 - fr[..., None]) + p1 * fr[..., None]
    pix[..., :3] *= shade[None, :, None]
    out = pix
    return Image.fromarray(out.clip(0, 255).astype(np.uint8), "RGBA")

def soft_shadow(im, blur=30, op=0.6):
    a = im.getchannel("A").point(lambda v: int(v * op))
    sh = Image.new("RGBA", (im.width + blur * 4, im.height + blur * 4), (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (0, 0, 0, 255)); blk.putalpha(a)
    sh.alpha_composite(blk, (blur * 2, blur * 2))
    return sh.filter(ImageFilter.GaussianBlur(blur))

# ---------- clock ----------
def clock_img(R, hh, mm, ss, sec_col=WHITE, ring=WHITE):
    S = 3
    size = (R * 2 + 40) * S
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = size / 2; r = R * S
    d.ellipse([c - r, c - r, c + r, c + r], outline=ring + (230,), width=3 * S)
    for i in range(60):
        a = math.radians(i * 6 - 90)
        big = i % 5 == 0
        r1 = r * (0.86 if big else 0.92); r2 = r * 0.96
        d.line([c + r1 * math.cos(a), c + r1 * math.sin(a), c + r2 * math.cos(a), c + r2 * math.sin(a)],
               fill=ring + (230 if big else 110,), width=(4 if big else 2) * S)
    def hand(deg, length, width, col, tail=0.12):
        a = math.radians(deg - 90)
        d.line([c - r * tail * math.cos(a), c - r * tail * math.sin(a),
                c + r * length * math.cos(a), c + r * length * math.sin(a)], fill=col, width=int(width * S))
    hand((hh % 12 + mm / 60) * 30, 0.5, 9, WHITE + (255,))
    hand((mm + ss / 60) * 6, 0.78, 6, WHITE + (255,))
    hand(ss * 6, 0.86, 2.5, sec_col + (255,), tail=0.2)
    d.ellipse([c - 9 * S, c - 9 * S, c + 9 * S, c + 9 * S], fill=sec_col + (255,))
    return im.resize((size // S, size // S), Image.LANCZOS)

def ease(x):
    x = max(0, min(1, x)); return x * x * (3 - 2 * x)

def fade(t, a, b, c=None, d=None):
    """0 before a, ramps to 1 at b, holds, ramps down c->d"""
    v = ease((t - a) / (b - a)) if b > a else (1 if t >= a else 0)
    if c is not None: v *= 1 - ease((t - c) / (d - c))
    return v
