"""Right Direction — моушн-ролик логотипа.

Сценарий «Поиск верного курса» (9.5 с, 1920x1080, 60 fps):
  0.00–1.55  Тёмная «карта»: сетка, компас, пыль. Синяя комета ищет курс —
             её траектория колеблется (пинги сонара на каждом гребне) и
             затухает, выстраиваясь точно по оси синего штриха, который она
             «прорисовывает». Кольцо компаса доворачивает метку на этот курс.
  1.55       Фиксация курса: вспышка, ударная волна, металлический «лок».
  1.62–2.30  Белая волна света разворачивается из точки фиксации.
  2.00–2.85  Три тёмно-синие грани «R» влетают по своим осям и встают на место.
  2.95–3.40  Блик пробегает по знаку.
  2.95–4.40  Камера отъезжает к полной композиции.
  3.45–3.85  Разделитель вырастает из центра.
  3.70–4.60  Буквы RIGHT / DIRECTION выезжают из-за разделителя.
  4.55–5.30  CONSULTING «раздвигает» трекинг.
  5.35–6.40  STRATEGY / TRANSFORMATION / RESULTS поднимаются по нотам до-ми-соль.
  6.30–6.60  Импульс света бежит по синему штриху к острию.
  6.60       Финальный аккорд, искры по направлению стрелки, общий блик.
  6.60–9.50  Удержание, лёгкий наезд камеры.

Запуск:  py -3.12 make_motion.py <logo.png> <out_dir> [video|audio|stills t1,t2,...]
"""
import sys, os, math, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SRC, OUTDIR = sys.argv[1], sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else 'video'
os.makedirs(OUTDIR, exist_ok=True)

FPS, DUR = 60, 9.5
OW, OH = 1920, 1080
S, MX, MY = 2, 380, 110                    # мир = (src + M) * S
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, t0, d): return clamp((t - t0) / d)
def lerp(a, b, u): return a + (b - a) * u
def e_out_cubic(u): return 1 - (1 - u) ** 3
def e_in_cubic(u): return u ** 3
def e_inout_cubic(u): return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2
def e_out_expo(u): return 1.0 if u >= 1 else 1 - 2 ** (-10 * u)
def e_out_back(u, c1=1.70158): return 1 + (c1 + 1) * (u - 1) ** 3 + c1 * (u - 1) ** 2
def W(x, y): return ((x + MX) * S, (y + MY) * S)

# ---------------------------------------------------------------- timeline
T_C0, T_LOCK = 0.35, 1.55
T_W0, T_W1 = 1.62, 2.30
PIECES = [('left', 2.00, .45), ('leg', 2.15, .45), ('top', 2.30, .55)]
T_GLEAM = (2.95, .45)
T_PULL = (2.95, 1.45)
T_DIV = (3.45, .40)
T_RIGHT, T_DIRECTION, LETTER_STAGGER, LETTER_DUR = 3.70, 3.95, .055, .65
T_CONS, CONS_DUR = 4.55, .75
TAG = [('STRATEGY', 5.35), ('/1', 5.55), ('TRANSFORMATION', 5.65), ('/2', 5.85), ('RESULTS', 5.95)]
TAG_DUR = .45
T_PULSE, T_HIT = 6.30, 6.60
T_GLINT = (6.70, .65)
T_STATIC = 6.45

# ---------------------------------------------------------------- слои из PNG
src = np.asarray(Image.open(SRC).convert('RGB')).astype(np.float32)
SH, SW = src.shape[:2]
WW, WH = (SW + 2 * MX) * S, (SH + 2 * MY) * S
alpha = (255 - src.min(axis=2)) / 255.0                 # color-to-alpha от белого
alpha[alpha < 0.03] = 0
col = np.clip(255 - (255 - src) / np.maximum(alpha, 1e-3)[..., None], 0, 255)
RGBA = np.dstack([col, alpha * 255]).astype(np.uint8)

m = alpha > 0.2
m[:, 520:] = False
lab = Image.fromarray((m * 255).astype(np.uint8)).copy()
labels = {}
for i, (k, xy) in enumerate({'top': (300, 330), 'left': (220, 470), 'blue': (200, 640)}.items()):
    ImageDraw.floodfill(lab, xy, 10 + 40 * i)
    labels[k] = np.asarray(lab) == 10 + 40 * i
rows = np.arange(SH)[:, None]
labels['leg'] = labels['top'] & (rows >= 506)
labels['top'] = labels['top'] & ~labels['leg']
edge = (alpha > 0) & ~m
edge[:, 520:] = False
def dil(mk): return np.asarray(Image.fromarray((mk * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
assigned = np.zeros_like(m)
masks = {}
for k in ['blue', 'left', 'leg', 'top']:
    masks[k] = labels[k] | (dil(labels[k]) & edge & ~assigned)
    assigned |= masks[k]

def make_layer(mask):
    ys, xs = np.where(mask)
    x0, y0, x1, y1 = xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3
    crop = RGBA[y0:y1, x0:x1].copy()
    crop[..., 3] = (crop[..., 3] * mask[y0:y1, x0:x1]).astype(np.uint8)
    im = Image.fromarray(crop, 'RGBA').resize(((x1 - x0) * S, (y1 - y0) * S), Image.LANCZOS)
    arr = np.asarray(im).copy()
    a = np.clip((arr[..., 3] / 255.0 - .5) * 1.2 + .5, 0, 1)
    arr[..., 3] = (a * 255).astype(np.uint8)
    return dict(img=Image.fromarray(arr, 'RGBA'), x0=x0, y0=y0, x1=x1, y1=y1,
                cx=(x0 + x1) / 2, cy=(y0 + y1) / 2)

def box_mask(x0, x1, y0, y1):
    mk = np.zeros_like(m)
    mk[y0:y1, x0:x1] = alpha[y0:y1, x0:x1] > 0
    return mk

def letter_runs(y0, y1, x0=585, x1=1440):
    v = (alpha[y0:y1, x0:x1] > .25).any(axis=0)
    idx = np.where(v)[0]
    runs, s, p = [], idx[0], idx[0]
    for i in idx[1:]:
        if i - p > 2: runs.append((s + x0, p + x0)); s = i
        p = i
    runs.append((s + x0, p + x0))
    out = []
    for i, (a, b) in enumerate(runs):
        l = (runs[i - 1][1] + a) // 2 + 1 if i else a - 3
        r = (b + runs[i + 1][0]) // 2 if i < len(runs) - 1 else b + 4
        out.append((l, r))
    return out

L = {k: make_layer(masks[k]) for k in masks}
L['div'] = make_layer(box_mask(528, 549, 285, 700))
RIGHT = [make_layer(box_mask(a, b, 288, 410)) for a, b in letter_runs(288, 410)]
DIRECTION = [make_layer(box_mask(a, b, 419, 540)) for a, b in letter_runs(419, 540)]
CONS = [make_layer(box_mask(a, b, 569, 625)) for a, b in letter_runs(569, 625)]
TAGX = {'STRATEGY': (598, 792), '/1': (800, 840), 'TRANSFORMATION': (850, 1200),
        '/2': (1210, 1252), 'RESULTS': (1262, 1428)}
TAGL = {k: make_layer(box_mask(a, b, 674, 711)) for k, (a, b) in TAGX.items()}
assert len(RIGHT) == 5 and len(DIRECTION) == 9 and len(CONS) == 10, (len(RIGHT), len(DIRECTION), len(CONS))

def pca(mask):
    ys, xs = np.where(mask)
    pts = np.stack([xs, ys], 1).astype(float)
    c = pts.mean(0)
    w, v = np.linalg.eigh(np.cov((pts - c).T))
    return c, v[:, np.argmax(w)], pts

c_b, D, pts = pca(masks['blue'])
if D[0] < 0: D = -D
proj = (pts - c_b) @ D
P0 = c_b + D * proj.min()
LB = proj.max() - proj.min()
TIP = c_b + D * proj.max()
NRM = np.array([-D[1], D[0]])
if NRM[1] < 0: NRM = -NRM
_, D_LEFT, _ = pca(masks['left'])
if D_LEFT[0] < 0: D_LEFT = -D_LEFT
_, D_LEG, _ = pca(masks['leg'])
if D_LEG[1] < 0: D_LEG = -D_LEG
MARK_C = np.array([298.0, 491.0])
FINAL_C = np.array([769.0, 499.0])
XCLIP = 547.0

# ---------------------------------------------------------------- рендер-хелперы
def comp(cv, tile, x, y):
    Wc, Hc = cv.size; w, h = tile.size
    if x >= Wc or y >= Hc or x + w <= 0 or y + h <= 0: return
    cx0, cy0 = max(0, -x), max(0, -y)
    cx1, cy1 = min(w, Wc - x), min(h, Hc - y)
    if (cx0, cy0, cx1, cy1) != (0, 0, w, h): tile = tile.crop((cx0, cy0, cx1, cy1))
    cv.alpha_composite(tile, (x + cx0, y + cy0))

def place(cv, Ly, dx=0.0, dy=0.0, sc=1.0, rot=0.0, op=1.0, clip=None):
    if op <= 0.003: return
    img = Ly['img']; w, h = img.size
    cxw, cyw = W(Ly['cx'] + dx, Ly['cy'] + dy)
    th = math.radians(rot); co, si = math.cos(th) * sc, math.sin(th) * sc
    pts_ = [(cxw + co * x - si * y, cyw + si * x + co * y)
            for x, y in [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]]
    bx0 = math.floor(min(p[0] for p in pts_)) - 1; by0 = math.floor(min(p[1] for p in pts_)) - 1
    bx1 = math.ceil(max(p[0] for p in pts_)) + 1; by1 = math.ceil(max(p[1] for p in pts_)) + 1
    det = co * co + si * si; ia, ib = co / det, si / det
    coeffs = (ia, ib, w / 2 + ia * (bx0 - cxw) + ib * (by0 - cyw),
              -ib, ia, h / 2 - ib * (bx0 - cxw) + ia * (by0 - cyw))
    if rot == 0 and sc == 1 and float(cxw - w / 2).is_integer() and float(cyw - h / 2).is_integer():
        tile, bx0, by0 = img, int(cxw - w / 2), int(cyw - h / 2)
    else:
        tile = img.transform((bx1 - bx0, by1 - by0), Image.AFFINE, coeffs, resample=Image.BICUBIC)
    if op < 1 or clip:
        arr = np.asarray(tile).copy()
        a = arr[..., 3].astype(np.float32) * op
        if clip: a = clip(a, bx0, by0)
        arr[..., 3] = np.clip(a, 0, 255).astype(np.uint8)
        tile = Image.fromarray(arr, 'RGBA')
    comp(cv, tile, bx0, by0)

def clip_xmin(xs):
    def f(a, bx, by):
        k = int(round((xs + MX) * S - bx))
        if k > 0: a[:, :k] = 0
        return a
    return f

def clip_ymax(ys):
    def f(a, bx, by):
        k = int(round((ys + MY) * S - by))
        if k < a.shape[0]: a[max(k, 0):, :] = 0
        return a
    return f

def clip_yband(y0, y1):
    def f(a, bx, by):
        k0 = int(round((y0 + MY) * S - by)); k1 = int(round((y1 + MY) * S - by))
        a[:max(k0, 0), :] = 0
        if k1 < a.shape[0]: a[max(k1, 0):, :] = 0
        return a
    return f

def clip_axis(s_cur):
    def f(a, bx, by):
        h, w = a.shape
        X = (bx + np.arange(w)) / S - MX; Y = (by + np.arange(h)) / S - MY
        pr = (X[None, :] - P0[0]) * D[0] + (Y[:, None] - P0[1]) * D[1]
        return a * np.clip((s_cur - pr) / 5 + .5, 0, 1)
    return f

def sprite(rad, color, sigma):
    n = int(rad * 2)
    y, x = np.mgrid[0:n, 0:n] - rad + .5
    arr = np.zeros((n, n, 4), np.uint8)
    arr[..., :3] = color
    arr[..., 3] = (np.exp(-(x * x + y * y) / (2 * sigma * sigma)) * 255).astype(np.uint8)
    return Image.fromarray(arr, 'RGBA')

def put_sprite(cv, spr, xs, ys, scale=1.0, op=1.0):
    if op <= .003 or scale <= .01: return
    n = max(2, int(spr.size[0] * scale))
    im = spr.resize((n, n), Image.BILINEAR) if n != spr.size[0] else spr
    if op < 1:
        arr = np.asarray(im).copy(); arr[..., 3] = (arr[..., 3] * min(op, 1)).astype(np.uint8)
        im = Image.fromarray(arr, 'RGBA')
    wx, wy = W(xs, ys)
    comp(cv, im, int(wx - n / 2), int(wy - n / 2))

GLOW = sprite(120, (70, 160, 255), 34)
CORE = sprite(24, (235, 245, 255), 6)
FLASH = sprite(260, (150, 205, 255), 70)

# --- фоны
Xs = (np.arange(WW, dtype=np.float32) / S - MX)
Ys = (np.arange(WH, dtype=np.float32) / S - MY)
dist = np.sqrt((Xs[None, :] - MARK_C[0]) ** 2 + (Ys[:, None] - MARK_C[1]) ** 2)
v = np.clip(dist / 950, 0, 1) ** 1.2
c0, c1 = np.array([13, 40, 72], np.float32), np.array([2, 8, 17], np.float32)
dark = c0[None, None, :] * (1 - v[..., None]) + c1[None, None, :] * v[..., None]
gx = (np.mod(Xs, 64) < .75)[None, :]; gy = (np.mod(Ys, 64) < .75)[:, None]
gridm = (gx | gy).astype(np.float32) * (1 - v) * .35
dark = dark * (1 - gridm[..., None]) + np.array([40, 95, 150], np.float32) * gridm[..., None]
DARK = Image.fromarray(np.dstack([dark, np.full(dist.shape, 255, np.float32)]).astype(np.uint8), 'RGBA')
lg = np.full((WH, WW, 3), 255, np.float32)
gm2 = (gx | gy).astype(np.float32) * .55
lg = lg * (1 - gm2[..., None]) + np.array([225, 233, 243], np.float32) * gm2[..., None]
LIGHT_GRID = Image.fromarray(np.dstack([lg, np.full(dist.shape, 255, np.float32)]).astype(np.uint8), 'RGBA')
LIGHT = Image.new('RGBA', (WW, WH), (255, 255, 255, 255))
del dist, v, dark, lg, gridm, gm2

def light_now(t):
    g = 1 - prog(t, 2.6, .9)
    if g >= 1: return LIGHT_GRID.copy()
    if g <= 0: return LIGHT.copy()
    return Image.blend(LIGHT, LIGHT_GRID, g)

# --- компас (рисуется с суперсэмплингом)
ANG_D = math.degrees(math.atan2(D[1], D[0]))
def make_compass():
    R0 = 450; n = (2 * R0 + 40) * S; ss = 2; N = n * ss
    im = Image.new('RGBA', (N, N), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    c = N / 2; k = S * ss
    colr = (90, 150, 215, 120)
    def circ(r, wdt, colr_=colr): dr.ellipse((c - r * k, c - r * k, c + r * k, c + r * k), outline=colr_, width=int(wdt * k))
    circ(270, 1.0)
    circ(345, 1.2)
    for a in range(0, 360, 5):
        r2 = 345 + (26 if a % 45 == 0 else 10)
        ar = math.radians(a)
        dr.line((c + 345 * k * math.cos(ar), c + 345 * k * math.sin(ar), c + r2 * k * math.cos(ar), c + r2 * k * math.sin(ar)),
                fill=colr if a % 45 else (120, 180, 235, 170), width=int((1.6 if a % 45 == 0 else 1) * k))
    for a in range(0, 360, 4):
        dr.arc((c - 430 * k, c - 430 * k, c + 430 * k, c + 430 * k), a, a + 2, fill=(90, 150, 215, 80), width=int(1 * k))
    ar = math.radians(ANG_D)
    tipp = (c + 405 * k * math.cos(ar), c + 405 * k * math.sin(ar))
    b1 = (c + 375 * k * math.cos(ar + .05), c + 375 * k * math.sin(ar + .05))
    b2 = (c + 375 * k * math.cos(ar - .05), c + 375 * k * math.sin(ar - .05))
    dr.polygon([tipp, b1, b2], fill=(60, 150, 255, 235))
    return im.resize((n, n), Image.LANCZOS)
COMPASS = make_compass()

DUST = [dict(x=rng.uniform(-320, 960), y=rng.uniform(120, 900), r=rng.uniform(.8, 2.4),
             a=rng.uniform(40, 150), f=rng.uniform(.5, 2.0), ph=rng.uniform(0, 6.28), vy=rng.uniform(-14, -4))
        for _ in range(150)]

# --- комета
def comet_s(t):
    u = prog(t, T_C0, T_LOCK - T_C0)
    return -430 + (430 + LB) * (.45 * u + .55 * u * u)
def comet_pos(s):
    A = 115 * clamp(-s / 430) ** 1.2
    lat = A * math.sin(2 * math.pi * (s + 430) / 200)
    return P0 + D * s + NRM * lat
def t_of_s(s):
    lo, hi = T_C0, T_LOCK
    for _ in range(50):
        mid = (lo + hi) / 2
        if comet_s(mid) < s: lo = mid
        else: hi = mid
    return lo
PINGS = [(t_of_s(sk), comet_pos(sk)) for sk in [-380, -280, -180, -80]]

# --- искры финала
SPARKS = []
for i in range(30):
    ang = math.radians(ANG_D) + rng.normal(0, .42)
    sp = rng.uniform(260, 820)
    SPARKS.append(dict(v=np.array([math.cos(ang), math.sin(ang)]) * sp, life=rng.uniform(.5, 1.15),
                       w=rng.uniform(3.0, 6.0), c=[(10, 106, 200), (60, 150, 255), (140, 195, 255)][i % 3],
                       d=rng.uniform(0, .08)))
def spark_pos(sk, tt_):
    k = 3.2
    return TIP + sk['v'] * (1 - math.exp(-k * tt_)) / k

# --- синее свечение для тёмной фазы
def glow_layer(Ly, pad=50, blur=16, color=(47, 139, 255), gain=.85):
    w, h = Ly['img'].size
    big = Image.new('RGBA', (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    a = Ly['img'].split()[3]
    solid = Image.new('RGBA', (w, h), color + (255,)); solid.putalpha(a)
    big.paste(solid, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    arr = np.asarray(big).copy(); arr[..., 3] = (arr[..., 3] * gain).astype(np.uint8)
    return dict(img=Image.fromarray(arr, 'RGBA'), cx=Ly['cx'], cy=Ly['cy'])
BLUE_GLOW = glow_layer(L['blue'])

# --- статичный финальный логотип и маски для бликов
ALL_LAYERS = [L['blue'], L['left'], L['leg'], L['top'], L['div']] + RIGHT + DIRECTION + CONS + list(TAGL.values())
static = Image.new('RGBA', (WW, WH), (0, 0, 0, 0))
for Ly in ALL_LAYERS: place(static, Ly)
SB = static.getbbox()
STATIC = static.crop(SB)
blue_only = Image.new('RGBA', (WW, WH), (0, 0, 0, 0)); place(blue_only, L['blue'])

def region(img_alpha_src, bbox):
    x0, y0, x1, y1 = bbox
    a = np.asarray(img_alpha_src.crop(bbox))[..., 3].astype(np.float32) / 255
    X = (x0 + np.arange(x1 - x0, dtype=np.float32)) / S - MX
    Y = (y0 + np.arange(y1 - y0, dtype=np.float32)) / S - MY
    return dict(a=a, X=X, Y=Y, x0=x0, y0=y0)
mx1 = int(W(520, 0)[0])
R_MARK = region(static, (SB[0], SB[1], mx1, SB[3]))
R_ALL = region(static, SB)
R_BLUE = region(blue_only, blue_only.getbbox())

def gleam(cv, R, uc, width, strength, color=(255, 255, 255), dirv=(1.0, .55), axis=False):
    if axis:
        U = (R['X'][None, :] - P0[0]) * D[0] + (R['Y'][:, None] - P0[1]) * D[1]
    else:
        U = R['X'][None, :] * dirv[0] + R['Y'][:, None] * dirv[1]
    a = R['a'] * np.exp(-((U - uc) / width) ** 2) * strength
    if a.max() < .004: return
    arr = np.zeros(a.shape + (4,), np.uint8); arr[..., :3] = color; arr[..., 3] = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    comp(cv, Image.fromarray(arr, 'RGBA'), R['x0'], R['y0'])
def urange(R, dirv=(1.0, .55)):
    return float(R['X'].min() * dirv[0] + R['Y'].min() * dirv[1]), float(R['X'].max() * dirv[0] + R['Y'].max() * dirv[1])

# ---------------------------------------------------------------- тайминги событий (для звука и тряски)
def impact_time(t0, dur): return t0 + .37 * dur
IMPACTS = [(n, impact_time(t0, d)) for n, t0, d in PIECES]

def order_far_first(letters):
    return sorted(range(len(letters)), key=lambda i: -letters[i]['x0'])
LETTER_EVENTS = []
for letters, t0 in [(RIGHT, T_RIGHT), (DIRECTION, T_DIRECTION)]:
    for rank, i in enumerate(order_far_first(letters)):
        letters[i]['t0'] = t0 + rank * LETTER_STAGGER
        LETTER_EVENTS.append((letters[i]['t0'] + .04, letters[i]['cx']))
CONS_C = (CONS[0]['x0'] + CONS[-1]['x1']) / 2
for Ly in CONS:
    Ly['t0'] = T_CONS + abs(Ly['cx'] - CONS_C) / 340 * .18

def camera(t):
    u0 = e_inout_cubic(prog(t, 0, T_PULL[0]))
    z = lerp(1.62, 1.80, u0)
    c = MARK_C + np.array([lerp(-80, 0, u0), lerp(110, 0, u0)])
    u = e_inout_cubic(prog(t, *T_PULL))
    z = math.exp(lerp(math.log(z), math.log(1.12), u))
    c = c * (1 - u) + FINAL_C * u
    z *= 1 + .03 * e_out_cubic(prog(t, T_HIT, DUR - T_HIT))
    sh = np.zeros(2)
    for amp, ti in [(2.6, IMPACTS[0][1]), (2.6, IMPACTS[1][1]), (3.4, IMPACTS[2][1]), (2.0, T_LOCK), (1.4, T_HIT)]:
        if t > ti:
            k = math.exp(-(t - ti) * 11) * amp
            sh += k * np.array([math.sin((t - ti) * 71), math.cos((t - ti) * 57)])
    return c + sh, z

def pan_of(xs, t):
    c, z = camera(t)
    return clamp(((xs - c[0]) * z) / 960, -1, 1) * .8

# ---------------------------------------------------------------- кадр
def render(t):
    c, z = camera(t)
    # ФОН
    if t < T_W1:
        cv = DARK.copy()
        dr = ImageDraw.Draw(cv, 'RGBA')
        da = prog(t, 0, .8)
        for p in DUST:
            x, y = W(p['x'], p['y'] + p['vy'] * t)
            r = p['r'] * S
            a = p['a'] * da * (.55 + .45 * math.sin(p['ph'] + t * p['f'] * 6.28))
            dr.ellipse((x - r, y - r, x + r, y + r), fill=(150, 195, 255, int(a)))
        rot = 75 * (1 - e_inout_cubic(prog(t, 0, T_LOCK)))
        cop = prog(t, .1, .9) * (1 + 1.2 * math.exp(-max(0, t - T_LOCK) * 6) * (t > T_LOCK))
        comp_im = COMPASS.rotate(rot, Image.BICUBIC) if rot > .01 else COMPASS
        if cop < 1 or cop > 1:
            arr = np.asarray(comp_im).copy(); arr[..., 3] = np.clip(arr[..., 3] * cop, 0, 255).astype(np.uint8)
            comp_im = Image.fromarray(arr, 'RGBA')
        wx, wy = W(*MARK_C)
        comp(cv, comp_im, int(wx - comp_im.size[0] / 2), int(wy - comp_im.size[1] / 2))
        if t >= T_W0:
            Rw = 1800 * prog(t, T_W0, T_W1 - T_W0) ** 1.7
            mk = Image.new('L', (WW, WH), 0)
            cx_, cy_ = W(*TIP); rr = Rw * S
            ImageDraw.Draw(mk).ellipse((cx_ - rr, cy_ - rr, cx_ + rr, cy_ + rr), fill=255)
            cv = Image.composite(light_now(t), cv, mk)
    else:
        cv = light_now(t)
    dr = ImageDraw.Draw(cv, 'RGBA')

    # КОМЕТА
    if T_C0 <= t < T_LOCK + .35:
        tc = min(t, T_LOCK)
        fade = 1 - prog(t, T_LOCK, .3)
        taus = np.linspace(max(T_C0, tc - .75), tc, 60)
        pts_ = [W(*comet_pos(comet_s(x))) for x in taus]
        xs_ = [p[0] for p in pts_]; ys_ = [p[1] for p in pts_]
        bx0, by0 = int(min(xs_)) - 80, int(min(ys_)) - 80
        bx1, by1 = int(max(xs_)) + 80, int(max(ys_)) + 80
        tile = Image.new('RGBA', (bx1 - bx0, by1 - by0), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile, 'RGBA')
        n = len(pts_)
        for i in range(1, n):
            k = i / (n - 1)
            td.line((pts_[i - 1][0] - bx0, pts_[i - 1][1] - by0, pts_[i][0] - bx0, pts_[i][1] - by0),
                    fill=(70, 160, 255, int(255 * k ** 1.5 * fade)), width=max(1, int((2 + 9 * k) * S)))
        glow = tile.filter(ImageFilter.GaussianBlur(12))
        comp(cv, glow, bx0, by0); comp(cv, glow, bx0, by0)
        core = Image.new('RGBA', tile.size, (0, 0, 0, 0)); cd = ImageDraw.Draw(core, 'RGBA')
        for i in range(1, n):
            k = i / (n - 1)
            cd.line((pts_[i - 1][0] - bx0, pts_[i - 1][1] - by0, pts_[i][0] - bx0, pts_[i][1] - by0),
                    fill=(215, 235, 255, int(230 * k ** 2 * fade)), width=max(1, int((.8 + 3.2 * k) * S)))
        comp(cv, core, bx0, by0)
        if t < T_LOCK:
            hp = comet_pos(comet_s(t))
            put_sprite(cv, GLOW, hp[0], hp[1], 1.0, .9)
            put_sprite(cv, CORE, hp[0], hp[1], 1.0, 1)
    for tp, pp in PINGS:
        if tp <= t < tp + .7:
            u = (t - tp) / .7
            r = (8 + 80 * e_out_cubic(u)) * S
            x, y = W(*pp)
            dr.ellipse((x - r, y - r, x + r, y + r), outline=(110, 180, 255, int(200 * (1 - u))), width=max(1, int(2 * S * (1 - u) + 1)))

    # СЛОИ
    if t >= T_STATIC:
        comp(cv, STATIC, SB[0], SB[1])
    else:
        if t >= T_C0:
            clip = clip_axis(comet_s(t)) if t < T_LOCK else None
            gop = prog(t, .9, .5) * (1 - prog(t, T_W0, .7))
            if gop > 0: place(cv, BLUE_GLOW, op=gop, clip=clip)
            place(cv, L['blue'], clip=clip)
        for name, t0, dur in PIECES:
            def tf(tt_):
                u = prog(tt_, t0, dur); e = e_out_back(u)
                if name == 'left': off = -D_LEFT * 380 * (1 - e); rot = 0
                elif name == 'leg': off = D_LEG * 380 * (1 - e); rot = 0
                else: off = np.array([0, -380 * (1 - e)]); rot = -10 * (1 - e)
                return u, off, rot
            u, off, rot = tf(t)
            if u <= 0: continue
            if u < .7:
                for k in (3, 2, 1):
                    tk = t - k * .022
                    uk, offk, rotk = tf(tk)
                    if uk > 0: place(cv, L[name], offk[0], offk[1], rot=rotk, op=.28 / k)
            place(cv, L[name], off[0], off[1], rot=rot, op=clamp(u * 6))
        u = prog(t, *T_DIV)
        if u > 0:
            e = e_out_cubic(u); y0, y1 = L['div']['y0'], L['div']['y1']; mid = (y0 + y1) / 2; half = (y1 - y0) / 2 * e
            place(cv, L['div'], clip=clip_yband(mid - half - 1, mid + half + 1))
            if u < 1:
                for yy in (mid - half, mid + half):
                    put_sprite(cv, GLOW, 538, yy, .35, (1 - u) * .9)
        for letters in (RIGHT, DIRECTION):
            for Ly in letters:
                u = prog(t, Ly['t0'], LETTER_DUR)
                if u <= 0: continue
                dx0 = XCLIP - Ly['x1']
                place(cv, Ly, dx0 * (1 - e_out_expo(u)), 0, clip=clip_xmin(XCLIP))
        for Ly in CONS:
            u = prog(t, Ly['t0'], CONS_DUR)
            if u <= 0: continue
            e = e_out_cubic(u)
            dx = (CONS_C + (Ly['cx'] - CONS_C) * lerp(.35, 1, e)) - Ly['cx']
            place(cv, Ly, dx, 10 * (1 - e), op=e)
        for k, t0 in TAG:
            u = prog(t, t0, TAG_DUR)
            if u <= 0: continue
            e = e_out_cubic(u)
            place(cv, TAGL[k], 0, 30 * (1 - e), op=clamp(u * 2.5), clip=clip_ymax(711))

    # БЛИКИ И ЭФФЕКТЫ
    u = prog(t, *T_GLEAM)
    if 0 < u < 1:
        a0, a1 = urange(R_MARK); gleam(cv, R_MARK, lerp(a0 - 80, a1 + 80, e_inout_cubic(u)), 38, .6)
    u = prog(t, T_PULSE, T_HIT - T_PULSE)
    if 0 < u < 1 or T_HIT <= t < T_HIT + .15:
        uc = LB * e_in_cubic(u) if t < T_HIT else LB
        gleam(cv, R_BLUE, uc, 22, .85 * (1 - prog(t, T_HIT, .15)), color=(215, 238, 255), axis=True)
    u = prog(t, *T_GLINT)
    if 0 < u < 1:
        a0, a1 = urange(R_ALL); gleam(cv, R_ALL, lerp(a0 - 120, a1 + 120, e_inout_cubic(u)), 60, .42)
    if T_LOCK - .03 <= t < T_LOCK + .8:
        k = math.exp(-max(0, t - T_LOCK) / .14) if t >= T_LOCK else (t - T_LOCK + .03) / .03
        put_sprite(cv, FLASH, TIP[0], TIP[1], .6 + .9 * k, k)
        put_sprite(cv, CORE, TIP[0], TIP[1], 2.5 * k, k)
        u = prog(t, T_LOCK, .65)
        r = (15 + 420 * e_out_cubic(u)) * S; x, y = W(*TIP)
        dr.ellipse((x - r, y - r, x + r, y + r), outline=(120, 190, 255, int(230 * (1 - u))), width=max(1, int(3 * S * (1 - u)) + 1))
    if T_W0 <= t < T_W1 + .1:
        u = prog(t, T_W0, T_W1 - T_W0)
        r = 1800 * u ** 1.7 * S; x, y = W(*TIP)
        dr.ellipse((x - r, y - r, x + r, y + r), outline=(47, 139, 255, int(220 * (1 - u))), width=int(5 * S))
    if T_HIT <= t < T_HIT + 1.4:
        u = prog(t, T_HIT, .8)
        if u < 1:
            r = (10 + 260 * e_out_cubic(u)) * S; x, y = W(*TIP)
            dr.ellipse((x - r, y - r, x + r, y + r), outline=(60, 150, 255, int(120 * (1 - u) ** 2)), width=max(1, int(2.5 * S * (1 - u)) + 1))
        put_sprite(cv, GLOW, TIP[0], TIP[1], .9, math.exp(-(t - T_HIT) / .12))
        for sk in SPARKS:
            tt_ = t - T_HIT - sk['d']
            if 0 < tt_ < sk['life']:
                p1 = spark_pos(sk, tt_); p2 = spark_pos(sk, max(0, tt_ - .07))
                fa = (1 - tt_ / sk['life']) ** 1.3
                (x1, y1), (x2, y2) = W(*p1), W(*p2)
                dr.line((x2, y2, x1, y1), fill=sk['c'] + (int(255 * fa),), width=max(1, int(sk['w'] * S * fa) + 1))

    # КАМЕРА
    x0w, y0w = W(c[0] - OW / 2 / z, c[1] - OH / 2 / z)
    out = cv.resize((OW, OH), Image.LANCZOS, box=(x0w, y0w, x0w + OW / z * S, y0w + OH / z * S)).convert('RGB')
    if t < .4:
        out = Image.blend(Image.new('RGB', (OW, OH), (0, 0, 0)), out, e_out_cubic(t / .4))
    return out

# ---------------------------------------------------------------- звук
SR = 48000
NS = int(SR * DUR)
def tt(d): return np.arange(int(d * SR)) / SR
def noise(d): return rng.standard_normal(int(d * SR))
def svf(x, f, q, mode='bp'):
    f = np.broadcast_to(np.asarray(f, dtype=float), x.shape)
    F = (2 * np.sin(np.pi * np.minimum(f, SR / 6) / SR)).tolist()
    damp = 1.0 / q; lp = bp = 0.0; out = [0.0] * len(x); xs = x.tolist()
    for i in range(len(xs)):
        hp = xs[i] - lp - damp * bp
        bp += F[i] * hp
        lp += F[i] * bp
        out[i] = bp if mode == 'bp' else (lp if mode == 'lp' else hp)
    return np.array(out)
def sweep(f0, f1, d, phase=0.0):
    t = tt(d); f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR + phase)
def att(n, a=.002):
    k = max(1, int(a * SR)); e = np.ones(n); e[:k] = np.linspace(0, 1, k); return e
def bell(f, d, tau=1.0, partials=((1, 1, 1), (2.0, .35, .5), (3.01, .18, .3), (5.4, .06, .15))):
    t = tt(d); s = np.zeros_like(t)
    for r, g, tf in partials: s += g * np.sin(2 * np.pi * f * r * t) * np.exp(-t / (tau * tf))
    return s * att(len(t))
def fm_bell(f, d, tau=1.5, idx=1.6, ratio=1.4):
    t = tt(d)
    return np.sin(2 * np.pi * f * t + idx * np.exp(-t / (tau * .3)) * np.sin(2 * np.pi * f * ratio * t)) * np.exp(-t / tau) * att(len(t), .003)
def marimba(f, d=.9):
    t = tt(d)
    return (np.sin(2 * np.pi * f * t) * np.exp(-t / .28) + .35 * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t / .05)
            + .15 * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t / .015)) * att(len(t), .001)

def synth_audio(path):
    dry = np.zeros((NS, 2)); wet = np.zeros((NS, 2))
    def add(sig, t0, pan=0.0, gain=1.0, rev=.25):
        if sig.ndim == 1:
            pan = np.asarray(pan, dtype=float)
            sig = np.stack([sig * np.cos((pan + 1) * np.pi / 4), sig * np.sin((pan + 1) * np.pi / 4)], 1)
        i0 = int(t0 * SR)
        if i0 < 0: sig = sig[-i0:]; i0 = 0
        n = min(len(sig), NS - i0)
        if n <= 0: return
        dry[i0:i0 + n] += sig[:n] * gain; wet[i0:i0 + n] += sig[:n] * gain * rev

    # 1. Дрон тёмной фазы
    d = 2.9; t = tt(d)
    env = np.clip(t / 1.0, 0, 1) ** 2 * np.clip((2.75 - t) / .55, 0, 1)
    lfo = .75 + .25 * np.sin(2 * np.pi * .55 * t)
    padL = sum(g * np.sin(2 * np.pi * f * t) for f, g in [(55, .5), (82.41, .32), (110, .22), (164.8, .1), (220.6, .05)])
    padR = sum(g * np.sin(2 * np.pi * f * 1.004 * t + .7) for f, g in [(55, .5), (82.41, .32), (110, .22), (164.8, .1), (220.6, .05)])
    add(np.stack([padL, padR], 1) * (env * lfo)[:, None], 0, gain=.22, rev=.35)
    wind = np.stack([svf(noise(d), 380 + 180 * np.sin(2 * np.pi * .3 * t), 1.2), svf(noise(d), 420 + 160 * np.cos(2 * np.pi * .27 * t), 1.2)], 1)
    add(wind * env[:, None], 0, gain=.10, rev=.3)

    # 2. Комета: свист, следующий за скоростью и позицией
    d = T_LOCK - T_C0 + .05; t = tt(d); u = np.clip(t / (T_LOCK - T_C0), 0, 1)
    f = 260 * (14 ** (u ** 1.6))
    wh = svf(noise(d), f, 1.8) * (u ** 1.1) * np.clip((d - t) / .05, 0, 1)
    pans = np.array([pan_of(comet_pos(comet_s(T_C0 + x))[0], T_C0 + x) for x in t[::480]])
    pan = np.interp(np.arange(len(t)), np.arange(len(pans)) * 480, pans)
    add(wh, T_C0, pan=pan, gain=.42, rev=.3)
    tone = sweep(180, 900, d) * (u ** 2) * np.clip((d - t) / .05, 0, 1)
    add(tone, T_C0, pan=pan, gain=.05, rev=.4)

    # 3. Пинги сонара на гребнях траектории
    for (tp, pp), fr in zip(PINGS, [659.26, 783.99, 880.0, 1046.5]):
        add(bell(fr, 1.4, tau=.55), tp, pan=pan_of(pp[0], tp), gain=.20, rev=.6)
        add(bell(fr * 2, .4, tau=.12), tp, pan=pan_of(pp[0], tp), gain=.05, rev=.6)

    # 4. Фиксация курса
    tl = T_LOCK; p = pan_of(TIP[0], tl)
    n = noise(.008); add(np.diff(n, prepend=0) * np.exp(-tt(.008) / .002), tl, p, .5, .2)
    add(np.sin(2 * np.pi * 2600 * tt(.05)) * np.exp(-tt(.05) / .01), tl, p, .22, .3)
    add(sweep(190, 42, .6) * np.exp(-tt(.6) / .17) * att(int(.6 * SR), .001), tl, 0, .95, .15)
    add(bell(392, 2.2, tau=1.3, partials=((1, 1, 1), (2.76, .5, .7), (5.40, .3, .45), (8.93, .15, .25))), tl, p, .16, .7)
    add(fm_bell(1567.98, 1.5, tau=.6), tl + .01, p, .08, .7)
    d = .9; t = tt(d)
    whoomp = np.stack([svf(noise(d), 2600 * (180 / 2600) ** (t / d), .9), svf(noise(d), 2400 * (170 / 2400) ** (t / d), .9)], 1)
    add(whoomp * (np.clip(t / .06, 0, 1) * np.exp(-t / .35))[:, None], T_W0 - .02, gain=.45, rev=.4)

    # 5. Грани «R»: свист + удар + тон
    for (name, ti), fr in zip(IMPACTS, [261.63, 329.63, 392.0]):
        p = pan_of(L[name]['cx'], ti)
        d = .22; t = tt(d)
        add(svf(noise(d), 700 * (6 ** (t / d)), 1.5) * (t / d) ** 2, ti - d, p, .28, .2)
        add(sweep(150, 52, .3) * np.exp(-tt(.3) / .07) * att(int(.3 * SR), .001), ti, p * .5, .75, .12)
        add(svf(noise(.08), 1100, 4) * np.exp(-tt(.08) / .02), ti, p, .55, .25)
        add(marimba(fr), ti, p, .22, .45)

    # 6. Блик по знаку
    g0, gd = T_GLEAM
    for i in range(14):
        ti = g0 + gd * (i / 13) ** .9 + rng.uniform(-.01, .01)
        add(np.sin(2 * np.pi * rng.uniform(4200, 9000) * tt(.12)) * np.exp(-tt(.12) / .025) * att(int(.12 * SR)), ti, lerp(-.6, .6, i / 13), .055, .6)
    t = tt(gd); add(sweep(1800, 4200, gd) * np.sin(np.pi * t / gd) ** 2, g0, 0, .03, .6)

    # 7. Отъезд камеры
    d = T_PULL[1]; t = tt(d); u = t / d
    pw = np.stack([svf(noise(d), 260 + 900 * np.sin(np.pi * u), .8), svf(noise(d), 280 + 860 * np.sin(np.pi * u), .8)], 1)
    add(pw * (np.sin(np.pi * u) ** 1.6)[:, None], T_PULL[0], gain=.18, rev=.35)

    # 8. Разделитель — «зип»
    d = T_DIV[1] + .05; t = tt(d); u = np.clip(t / T_DIV[1], 0, 1)
    add(svf(noise(d), 800 * (9 ** u), 5) * np.sin(np.pi * np.clip(u, 0, 1)) ** .7, T_DIV[0], pan_of(538, T_DIV[0]), .22, .3)
    add(sweep(600, 2400, d) * np.sin(np.pi * u) ** 2, T_DIV[0], 0, .04, .5)

    # 9. Буквы — мягкие механические щелчки
    for ti, xs in LETTER_EVENTS:
        p = pan_of(xs, ti)
        add(svf(noise(.03), rng.uniform(2400, 4200), 3) * np.exp(-tt(.03) / .006), ti, p, .2, .25)
        add(np.sin(2 * np.pi * rng.uniform(1500, 2200) * tt(.04)) * np.exp(-tt(.04) / .008), ti, p, .04, .3)

    # 10. CONSULTING — воздушная волна и стеклянные тона
    d = CONS_DUR + .3; t = tt(d); u = t / d
    add(np.stack([svf(noise(d), 1500 * (3.2 ** u), 1.3), svf(noise(d), 1600 * (3 ** u), 1.3)], 1) * (np.sin(np.pi * u) ** 2)[:, None], T_CONS, gain=.16, rev=.5)
    add(fm_bell(1046.5, 2.0, tau=.9, idx=.8), T_CONS + .1, -.3, .11, .8)
    add(fm_bell(1567.98, 2.0, tau=.9, idx=.8), T_CONS + .28, .3, .09, .8)

    # 11. Слоган — до, ми, соль
    notes = {'STRATEGY': 523.25, 'TRANSFORMATION': 659.26, 'RESULTS': 783.99}
    for k, t0 in TAG:
        p = pan_of(TAGL[k]['cx'], t0)
        if k in notes: add(marimba(notes[k], 1.2), t0 + .04, p, .30, .5)
        else: add(svf(noise(.03), 3500, 3) * np.exp(-tt(.03) / .005), t0 + .04, p, .12, .3)

    # 12. Райзер к финалу (обратная тарелка)
    d = T_HIT - 5.75; t = tt(d); u = t / d
    rs = np.stack([np.diff(noise(d), prepend=0), np.diff(noise(d), prepend=0)], 1)
    add(rs * (u ** 3.2)[:, None], 5.75, gain=.16, rev=.25)
    add(sweep(220, 880, d) * u ** 2.5, 5.75, 0, .05, .4)

    # 13. Финал: удар, аккорд, искры
    th = T_HIT
    add(sweep(72, 36, 2.2) * np.exp(-tt(2.2) / .55) * att(int(2.2 * SR), .002), th, 0, .9, .1)
    add(svf(noise(.35), 260, .7) * np.exp(-tt(.35) / .07), th, 0, .6, .3)
    add(np.diff(noise(.01), prepend=0) * np.exp(-tt(.01) / .002), th, pan_of(TIP[0], th), .4, .3)
    for f_, g, pn in [(65.41, .30, 0), (130.81, .22, -.1), (196.0, .14, .1)]:
        add(np.sin(2 * np.pi * f_ * tt(3.0)) * np.exp(-tt(3.0) / 1.3) * att(int(3.0 * SR), .01), th, pn, g, .4)
    for f_, g, pn, tau in [(261.63, .13, -.4, 2.4), (392.0, .12, .4, 2.2), (523.25, .12, -.2, 2.0),
                           (659.26, .11, .25, 1.8), (987.77, .08, -.5, 1.5), (1174.66, .07, .5, 1.3)]:
        add(fm_bell(f_, 2.9, tau=tau, idx=1.4), th + rng.uniform(0, .012), pn, g, .7)
    for sk in SPARKS:
        ti = th + sk['d'] + rng.uniform(0, .5) * sk['life']
        add(np.sin(2 * np.pi * rng.uniform(3000, 9000) * tt(.1)) * np.exp(-tt(.1) / .02) * att(int(.1 * SR)), ti, rng.uniform(-.8, .8), .045, .7)
    g0, gd = T_GLINT; t = tt(gd)
    add(sweep(2500, 6000, gd) * np.sin(np.pi * t / gd) ** 2, g0, 0, .025, .7)

    # Реверберация (стерео шумовой IR) и мастер
    n_ir = int(2.4 * SR); ti = np.arange(n_ir) / SR
    ir = rng.standard_normal((n_ir, 2)) * np.exp(-ti / .55)[:, None]
    ir[:int(.015 * SR)] = 0
    nfft = 1 << int(math.ceil(math.log2(NS + n_ir)))
    fr = np.fft.rfftfreq(nfft, 1 / SR); lpf = 1 / (1 + (fr / 5000) ** 2)
    out = dry.copy()
    for ch in range(2):
        IR = np.fft.rfft(ir[:, ch], nfft) * lpf
        rv = np.fft.irfft(np.fft.rfft(wet[:, ch], nfft) * IR, nfft)[:NS]
        out[:, ch] += rv / np.sqrt((ir[:, ch] ** 2).sum()) * .55
    out -= out.mean(0)
    out = np.tanh(out * 1.3) / 1.3
    fade = np.ones(NS); k = int(.3 * SR); fade[-k:] = np.linspace(1, 0, k) ** 2
    out *= fade[:, None]
    out = out / np.abs(out).max() * .89
    pcm = (out * 32767).astype('<i2')
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR); wf.writeframes(pcm.tobytes())

# ---------------------------------------------------------------- main
if MODE == 'stills':
    times = [float(x) for x in sys.argv[4].split(',')]
    for tv in times:
        render(tv).save(os.path.join(OUTDIR, f'still_{tv:05.2f}.png'))
        print('still', tv, flush=True)
elif MODE == 'audio':
    synth_audio(os.path.join(OUTDIR, 'sound.wav')); print('audio ok')
else:
    wav = os.path.join(OUTDIR, 'sound.wav')
    synth_audio(wav); print('audio ok', flush=True)
    mp4 = os.path.join(OUTDIR, 'right_direction_logo_motion.mp4')
    ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}',
                           '-r', str(FPS), '-i', '-', '-i', wav, '-c:v', 'libx264', '-preset', 'slow', '-crf', '16',
                           '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', mp4],
                          stdin=subprocess.PIPE)
    nf = int(DUR * FPS)
    for i in range(nf):
        ff.stdin.write(render(i / FPS).tobytes())
        if i % 60 == 0: print('frame', i, '/', nf, flush=True)
    ff.stdin.close(); ff.wait()
    print('done', mp4)
