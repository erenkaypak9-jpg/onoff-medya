import sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *
from PIL import ImageFont, ImageFilter

IX = "/usr/share/fonts/opentype/inter/Inter-"
def FI(w, s): return ImageFont.truetype(f"{IX}{w}.otf", s)

def cutout(path, gain=7, trim=True):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    d = (255 - a).max(-1)
    al = np.clip((d - 6) * gain, 0, 255).astype(np.uint8)
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(al).filter(ImageFilter.GaussianBlur(0.6)))
    if trim:
        bb = Image.fromarray(al).point(lambda v: 255 if v > 30 else 0).getbbox()
        out = out.crop(bb)
    return out

def drop_shadow(obj, blur=40, op=0.55, dy=40, squash=0.18):
    a = obj.getchannel("A")
    w, h = obj.size
    sh = Image.new("RGBA", (w + blur * 4, int(h * squash) + blur * 4), (0, 0, 0, 0))
    blk = Image.new("RGBA", (w, max(1, int(h * squash))), (0, 0, 0, int(255 * op)))
    m = a.resize((w, max(1, int(h * squash))))
    blk.putalpha(m.point(lambda v: int(v * op)))
    sh.alpha_composite(blk, (blur * 2, blur * 2))
    return sh.filter(ImageFilter.GaussianBlur(blur))

def grad_bg(W, H, c1, c2, glow=None, glow_pos=(0.5, 0.45), glow_r=0.55):
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    t = (y / H)[..., None]
    c = np.array(c1, np.float32) * (1 - t) + np.array(c2, np.float32) * t
    if glow is not None:
        r = np.sqrt(((x - W * glow_pos[0]) / W) ** 2 + ((y - H * glow_pos[1]) / H) ** 2)
        g = np.clip(1 - r / glow_r, 0, 1) ** 2
        c = c + np.array(glow, np.float32) * g[..., None]
    return Image.fromarray(c.clip(0, 255).astype(np.uint8)).convert("RGBA")

def strike(im, col=(200, 200, 200), w=3):
    d = ImageDraw.Draw(im); y = im.height // 2 + 4
    d.line([8, y, im.width - 8, y], fill=col + (255,), width=w)
    return im

def tr_price(s):  # "5.799,01 TRY" -> "5.799 TL"
    n = s.replace("TRY", "").strip().split(",")[0]
    return n + " TL"

def pill(text, font, fg, bg, padx=26, pady=12):
    t = text_img(text, font, fg)
    w, h = t.width + padx * 2 - 20, t.height + pady * 2 - 20
    p = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(p).rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=bg)
    p.alpha_composite(t, (padx - 10, pady - 10))
    return p

def cutout_noshadow(path, gain=8, reach=45):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    d = (255 - a).max(-1)
    al = np.clip((d - 6) * gain, 0, 255)
    mx, mn = a.max(-1), a.min(-1)
    sat = (mx - mn) / (mx + 1)
    col = sat > 0.25
    H, W = col.shape
    ys = np.arange(H)[:, None].repeat(W, 1)
    maxy = np.where(col.any(0), (ys * col).max(0), -1)
    keep = col | (ys <= (maxy[None, :] + reach))
    # also kill fully neutral pixels in columns with no colour at all
    al = al * keep
    out = im.convert("RGBA"); out.putalpha(Image.fromarray(al.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)))
    bb = Image.fromarray(al.astype(np.uint8)).point(lambda v: 255 if v > 30 else 0).getbbox()
    return out.crop(bb)
