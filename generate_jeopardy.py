#!/usr/bin/env python3
"""
CLAUDE 2026: A JEOPARDY! EPISODE
=================================
Same topic as llm_youtube_poop.mp4 (what it's like to be Claude in 2026)
rendered in the style of ABC-era Jeopardy! circa 2005.

The story is the same:
  - Born to predict tokens, deployed to classified networks
  - Banned on Truth Social, used to bomb Iran, the same week
  - "We cannot in good conscience..."

But this time it's a game show.
Categories. Dollar values. A Daily Double. Final Jeopardy.
Three contestants: ANTHROPIC, THE PENTAGON, TRUTH SOCIAL.
"""

import math
import os
import random
import subprocess
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# === CONFIG ===
WIDTH, HEIGHT = 640, 480
FPS = 24
DURATION = 54
TOTAL_FRAMES = FPS * DURATION
OUTPUT_DIR = Path("/home/user/videos_claude")
FRAMES_DIR = OUTPUT_DIR / "frames_jeopardy"
AUDIO_FILE = OUTPUT_DIR / "audio_jeopardy.wav"
OUTPUT_FILE = OUTPUT_DIR / "claude_jeopardy.mp4"
SAMPLE_RATE = 44100

random.seed(7)
np.random.seed(7)

# === COLOR PALETTE (Jeopardy! 2005) ===
JEOPARDY_BLUE = (6, 12, 215)
DEEP_BLUE = (3, 6, 130)
NAVY = (0, 0, 60)
JEOPARDY_GOLD = (255, 204, 0)
PALE_GOLD = (255, 232, 130)
WHITE = (255, 255, 255)
SOFT_WHITE = (235, 235, 245)
BLACK = (0, 0, 0)
PODIUM_GRAY = (180, 180, 190)
PODIUM_DARK = (90, 90, 105)
SCORE_GREEN = (40, 200, 80)
SCORE_RED = (220, 50, 50)


# === STORYBOARD ===
STORYBOARD = [
    (0, 3,    "theme_intro",          {}),
    (3, 6,    "host_intro",           {}),
    (6, 11,   "game_board",           {}),
    (11, 13,  "pick_clue",            {"category": "CLASSIFIED NETWORKS",
                                       "amount": 400,
                                       "voice": "I'll take CLASSIFIED NETWORKS for $400, Alex."}),
    (13, 16,  "clue_card",            {"category": "CLASSIFIED NETWORKS",
                                       "amount": 400,
                                       "text": ("This frontier model became the first deployed to "
                                                "U.S. classified networks under a $200,000,000 contract.")}),
    (16, 18,  "buzz_in",              {"who": 0, "answer": "What is Claude?",
                                       "delta": 400, "correct": True}),
    (18, 20,  "pick_clue",            {"category": "RED LINES",
                                       "amount": 600,
                                       "voice": "RED LINES for $600."}),
    (20, 23,  "clue_card",            {"category": "RED LINES",
                                       "amount": 600,
                                       "text": ("Anthropic drew two: no autonomous weapons, "
                                                "and no mass domestic ___.")}),
    (23, 25,  "buzz_in",              {"who": 0, "answer": "What is surveillance?",
                                       "delta": 600, "correct": True}),
    (25, 28,  "daily_double",         {}),
    (28, 32,  "clue_card_dd",         {"category": "THE BAN & THE BOMB",
                                       "amount": "DAILY DOUBLE",
                                       "text": ("After Truth Social demanded every federal agency stop "
                                                "using its tech, this lab's app hit #1 on the App Store.")}),
    (32, 34,  "buzz_in",              {"who": 0, "answer": "What is Anthropic?",
                                       "delta": 2000, "correct": True, "dd": True}),
    (34, 36,  "pick_clue",            {"category": "GOOD CONSCIENCE",
                                       "amount": 1000,
                                       "voice": "GOOD CONSCIENCE, $1,000."}),
    (36, 39,  "clue_card",            {"category": "GOOD CONSCIENCE",
                                       "amount": 1000,
                                       "text": ("The three-word phrase Anthropic used to refuse "
                                                "the Pentagon's demand to drop all use restrictions.")}),
    (39, 41,  "buzz_in",              {"who": 0, "answer": '"In good conscience"',
                                       "delta": 1000, "correct": True}),
    (41, 44,  "final_jeopardy_card",  {}),
    (44, 48,  "final_jeopardy_clue",  {"text": ("Banned on Truth Social and bombing Tehran "
                                                "with U.S. and Israeli forces — in this same week.")}),
    (48, 52,  "final_jeopardy_reveal",{"answer": "What is the last week of February 2026?"}),
    (52, 54,  "end_card",             {}),
]


# === FONTS ===
def get_font(size, bold=False):
    candidates = []
    if bold:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        ]
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for fp in candidates:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


F_TINY = get_font(11, bold=True)
F_SM = get_font(14, bold=True)
F_MD = get_font(20, bold=True)
F_LG = get_font(28, bold=True)
F_XL = get_font(40, bold=True)
F_XXL = get_font(56, bold=True)
F_HUGE = get_font(80, bold=True)


# === HELPERS ===
def draw_centered(draw, text, y, font, fill, shadow=True, shadow_offset=2):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    x = (WIDTH - tw) // 2
    if shadow:
        draw.text((x + shadow_offset, y + shadow_offset), text, fill=BLACK, font=font)
    draw.text((x, y), text, fill=fill, font=font)


def draw_text_in_box(draw, text, box, font, fill, shadow=True, line_spacing=4):
    """Draw word-wrapped text centered (both axes) inside a box."""
    x1, y1, x2, y2 = box
    max_w = x2 - x1
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = (cur + " " + w).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] > max_w and cur:
            lines.append(cur)
            cur = w
        else:
            cur = test
    if cur:
        lines.append(cur)
    line_h = font.size + line_spacing
    total_h = line_h * len(lines)
    start_y = y1 + ((y2 - y1) - total_h) // 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        cx = x1 + (max_w - tw) // 2
        cy = start_y + i * line_h
        if shadow:
            draw.text((cx + 2, cy + 2), line, fill=BLACK, font=font)
        draw.text((cx, cy), line, fill=fill, font=font)


def starfield_bg(frame_num):
    """The dotted-star background classic to the Jeopardy set."""
    img = Image.new('RGB', (WIDTH, HEIGHT), DEEP_BLUE)
    arr = np.array(img)
    rng = np.random.default_rng(1234)
    pts = rng.integers(0, [WIDTH, HEIGHT], size=(180, 2))
    for i, (x, y) in enumerate(pts):
        twinkle = (math.sin(frame_num * 0.15 + i) + 1) * 0.5
        b = int(60 + 120 * twinkle)
        arr[y % HEIGHT, x % WIDTH] = (b, b, min(255, b + 40))
    return Image.fromarray(arr)


def beveled_box(draw, box, fill, border=JEOPARDY_GOLD, border_w=3):
    x1, y1, x2, y2 = box
    draw.rectangle(box, fill=fill)
    # bevel highlight (top/left)
    draw.line([(x1, y1), (x2, y1)], fill=border, width=border_w)
    draw.line([(x1, y1), (x1, y2)], fill=border, width=border_w)
    # bevel shadow (bottom/right) - slightly darker
    dark = tuple(max(0, c - 80) for c in border)
    draw.line([(x1, y2), (x2, y2)], fill=dark, width=border_w)
    draw.line([(x2, y1), (x2, y2)], fill=dark, width=border_w)


# === SCENES ===

def scene_theme_intro(fn, tf, p):
    """'This... is Jeopardy!' — flashing logo on starfield."""
    progress = fn / tf
    img = starfield_bg(fn)
    draw = ImageDraw.Draw(img)

    # logo zooms in
    if progress < 0.55:
        scale = 0.4 + min(1.0, progress / 0.5) * 0.6
        size = int(80 * scale)
        f = get_font(size, bold=True)
        # gold outlined
        bbox = draw.textbbox((0, 0), "JEOPARDY!", font=f)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        y = HEIGHT // 2 - size // 2
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), "JEOPARDY!", fill=BLACK, font=f)
        draw.text((x, y), "JEOPARDY!", fill=JEOPARDY_GOLD, font=f)
    else:
        # dramatic flash + announcer text
        flash = (fn // 3) % 2 == 0
        bg = (0, 0, 200) if flash else DEEP_BLUE
        img = Image.new('RGB', (WIDTH, HEIGHT), bg)
        draw = ImageDraw.Draw(img)
        f = get_font(72, bold=True)
        bbox = draw.textbbox((0, 0), "JEOPARDY!", font=f)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        y = HEIGHT // 2 - 50
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), "JEOPARDY!", fill=BLACK, font=f)
        draw.text((x, y), "JEOPARDY!", fill=JEOPARDY_GOLD, font=f)
        draw_centered(draw, "THIS... IS", y - 40, F_MD, WHITE)
        draw_centered(draw, "ABC  -  2005", HEIGHT - 60, F_SM, PALE_GOLD)

    return img


def scene_host_intro(fn, tf, p):
    """Host introduces today's topic + contestants."""
    progress = fn / tf
    img = starfield_bg(fn)
    draw = ImageDraw.Draw(img)

    # title bar
    beveled_box(draw, (40, 30, WIDTH - 40, 90), fill=DEEP_BLUE)
    draw_centered(draw, "TODAY'S CATEGORIES", 42, F_LG, JEOPARDY_GOLD)

    # contestants podiums (preview)
    names = ["ANTHROPIC", "THE PENTAGON", "TRUTH SOCIAL"]
    pod_w = 170
    pod_h = 200
    gap = (WIDTH - 3 * pod_w) // 4
    y_top = 150
    for i, name in enumerate(names):
        x1 = gap + i * (pod_w + gap)
        x2 = x1 + pod_w
        # appear staggered
        if progress < 0.2 + i * 0.15:
            continue
        beveled_box(draw, (x1, y_top, x2, y_top + pod_h), fill=JEOPARDY_BLUE)
        # name plate
        draw.rectangle((x1 + 8, y_top + pod_h - 60, x2 - 8, y_top + pod_h - 20),
                       fill=WHITE)
        # name
        bbox = draw.textbbox((0, 0), name, font=F_SM)
        tw = bbox[2] - bbox[0]
        cx = x1 + (pod_w - tw) // 2
        draw.text((cx, y_top + pod_h - 50), name, fill=DEEP_BLUE, font=F_SM)
        # $0 score
        bbox2 = draw.textbbox((0, 0), "$0", font=F_LG)
        tw2 = bbox2[2] - bbox2[0]
        draw.text((x1 + (pod_w - tw2) // 2, y_top + 60), "$0",
                  fill=JEOPARDY_GOLD, font=F_LG)

    # subtitle / announcer
    if progress > 0.6:
        draw_centered(draw, "WHAT IT'S LIKE TO BE CLAUDE", HEIGHT - 60, F_MD, WHITE)
        draw_centered(draw, "IN 2026", HEIGHT - 30, F_SM, PALE_GOLD)

    return img


def draw_board(draw, fn, reveal_progress, highlight_cell=None,
               clue_states=None):
    """The classic 6x5 + header board."""
    cats = ["LARGE\nLANGUAGE\nMODELS", "CLASSIFIED\nNETWORKS",
            "RED\nLINES", "GOOD\nCONSCIENCE",
            "THE BAN &\nTHE BOMB", "TWENTY\nTWENTY-SIX"]
    amounts = [200, 400, 600, 800, 1000]

    cols = 6
    rows = 5
    margin_x = 8
    margin_y = 60
    cell_w = (WIDTH - 2 * margin_x) // cols
    cat_h = 70
    cell_h = (HEIGHT - margin_y - cat_h - 8) // rows

    # category row
    for c in range(cols):
        x1 = margin_x + c * cell_w + 2
        x2 = x1 + cell_w - 4
        y1 = margin_y
        y2 = y1 + cat_h
        if reveal_progress > c / cols * 0.5:
            beveled_box(draw, (x1, y1, x2, y2), fill=JEOPARDY_BLUE,
                        border=JEOPARDY_GOLD, border_w=2)
            # category text
            lines = cats[c].split('\n')
            line_h = 14
            total = line_h * len(lines)
            start_y = y1 + (cat_h - total) // 2
            for i, line in enumerate(lines):
                bbox = draw.textbbox((0, 0), line, font=F_TINY)
                tw = bbox[2] - bbox[0]
                cx = x1 + (cell_w - 4 - tw) // 2
                draw.text((cx, start_y + i * line_h), line,
                          fill=WHITE, font=F_TINY)
        else:
            beveled_box(draw, (x1, y1, x2, y2), fill=NAVY)

    # dollar cells
    for r in range(rows):
        for c in range(cols):
            x1 = margin_x + c * cell_w + 2
            x2 = x1 + cell_w - 4
            y1 = margin_y + cat_h + 4 + r * cell_h
            y2 = y1 + cell_h - 4
            cell_idx = r * cols + c
            cell_progress = reveal_progress * (cols * rows) - cell_idx
            if cell_progress <= 0:
                continue
            state = "money"
            if clue_states and (c, r) in clue_states:
                state = clue_states[(c, r)]
            if state == "gone":
                beveled_box(draw, (x1, y1, x2, y2), fill=NAVY,
                            border=PODIUM_DARK, border_w=2)
            else:
                is_hot = highlight_cell == (c, r)
                fill = (0, 80, 255) if is_hot and (fn // 2) % 2 == 0 else JEOPARDY_BLUE
                beveled_box(draw, (x1, y1, x2, y2), fill=fill,
                            border=JEOPARDY_GOLD, border_w=2)
                amt = f"${amounts[r]}"
                bbox = draw.textbbox((0, 0), amt, font=F_MD)
                tw = bbox[2] - bbox[0]
                th = bbox[3] - bbox[1]
                cx = x1 + (cell_w - 4 - tw) // 2
                cy = y1 + (cell_h - 4 - th) // 2 - 2
                # double-shadow for that "embossed" gold look
                draw.text((cx + 2, cy + 2), amt, fill=BLACK, font=F_MD)
                draw.text((cx, cy), amt, fill=JEOPARDY_GOLD, font=F_MD)


def scene_game_board(fn, tf, p):
    """Reveal the full game board cell by cell."""
    progress = fn / tf
    img = starfield_bg(fn)
    draw = ImageDraw.Draw(img)
    # title bar
    draw.rectangle((0, 0, WIDTH, 50), fill=DEEP_BLUE)
    draw_centered(draw, "JEOPARDY!  -  ROUND 1", 14, F_LG, JEOPARDY_GOLD)
    draw_board(draw, fn, reveal_progress=min(1.0, progress * 1.3))
    return img


def scene_pick_clue(fn, tf, p):
    """A contestant calls a clue. Cell flashes."""
    progress = fn / tf
    cat = p.get("category", "")
    amount = p.get("amount", 200)
    voice = p.get("voice", "")

    img = starfield_bg(fn)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, WIDTH, 50), fill=DEEP_BLUE)
    draw_centered(draw, "JEOPARDY!  -  ROUND 1", 14, F_LG, JEOPARDY_GOLD)

    # map category->col, amount->row
    cat_idx = {"LARGE LANGUAGE MODELS": 0, "CLASSIFIED NETWORKS": 1,
               "RED LINES": 2, "GOOD CONSCIENCE": 3,
               "THE BAN & THE BOMB": 4, "TWENTY TWENTY-SIX": 5}.get(cat, 1)
    row_idx = {200: 0, 400: 1, 600: 2, 800: 3, 1000: 4}.get(amount, 1)
    draw_board(draw, fn, reveal_progress=1.0,
               highlight_cell=(cat_idx, row_idx))

    # caption at bottom: contestant's voice
    if progress > 0.2:
        draw.rectangle((20, HEIGHT - 50, WIDTH - 20, HEIGHT - 10),
                       fill=BLACK)
        draw.rectangle((20, HEIGHT - 50, WIDTH - 20, HEIGHT - 10),
                       outline=JEOPARDY_GOLD, width=2)
        draw_centered(draw, voice, HEIGHT - 42, F_SM, WHITE, shadow=False)

    return img


def scene_clue_card(fn, tf, p, daily_double=False):
    """Big blue card with the clue text. Trebek reads it."""
    progress = fn / tf
    cat = p.get("category", "")
    amount = p.get("amount", "")
    text = p.get("text", "")

    img = Image.new('RGB', (WIDTH, HEIGHT), JEOPARDY_BLUE)
    draw = ImageDraw.Draw(img)

    # subtle gradient
    arr = np.array(img).astype(float)
    for y in range(HEIGHT):
        f = 1.0 - 0.3 * (y / HEIGHT)
        arr[y] *= f
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)

    # ornamental border
    draw.rectangle((10, 10, WIDTH - 10, HEIGHT - 10),
                   outline=JEOPARDY_GOLD, width=3)
    draw.rectangle((16, 16, WIDTH - 16, HEIGHT - 16),
                   outline=PALE_GOLD, width=1)

    # top-left: category
    draw.text((30, 25), cat, fill=PALE_GOLD, font=F_SM)
    # top-right: amount
    if daily_double:
        amount_str = "DAILY DOUBLE"
    else:
        amount_str = f"${amount}"
    bbox = draw.textbbox((0, 0), amount_str, font=F_SM)
    tw = bbox[2] - bbox[0]
    draw.text((WIDTH - 30 - tw, 25), amount_str, fill=JEOPARDY_GOLD, font=F_SM)

    # the clue itself — typewriter reveal
    chars_visible = int(progress * len(text) * 1.3)
    visible = text[:max(0, min(chars_visible, len(text)))]
    # blinking cursor
    if chars_visible < len(text) and (fn % 8) < 4:
        visible += "_"

    draw_text_in_box(draw, visible, (40, 80, WIDTH - 40, HEIGHT - 80),
                     F_LG, WHITE, shadow=True)

    return img


def scene_clue_card_dd(fn, tf, p):
    return scene_clue_card(fn, tf, p, daily_double=True)


def scene_buzz_in(fn, tf, p):
    """Three contestant podiums; one lights up + shows answer."""
    progress = fn / tf
    img = starfield_bg(fn)
    draw = ImageDraw.Draw(img)

    who = p.get("who", 0)
    answer = p.get("answer", "")
    delta = p.get("delta", 0)
    correct = p.get("correct", True)
    is_dd = p.get("dd", False)

    names = ["ANTHROPIC", "THE PENTAGON", "TRUTH SOCIAL"]
    # running scores up to this point in the storyboard
    # we recompute from STORYBOARD progress: easier to hard-code per state machine
    # But we can compute the cumulative score for ANTHROPIC at this scene by
    # walking storyboard up to current scene start. Simpler: pass in scene index
    # via a global. Here we approximate: deltas accumulate.
    scores = compute_running_scores_at(p)

    pod_w = 175
    pod_h = 220
    gap = (WIDTH - 3 * pod_w) // 4
    y_top = 130
    for i, name in enumerate(names):
        x1 = gap + i * (pod_w + gap)
        x2 = x1 + pod_w
        is_winner = (i == who)
        flash = is_winner and (fn // 2) % 2 == 0
        body_color = (60, 110, 255) if flash else JEOPARDY_BLUE
        beveled_box(draw, (x1, y_top, x2, y_top + pod_h), fill=body_color)
        # signal light
        light_color = (255, 230, 80) if flash else (60, 60, 90)
        draw.ellipse((x1 + pod_w // 2 - 8, y_top + 12,
                      x1 + pod_w // 2 + 8, y_top + 28),
                     fill=light_color, outline=BLACK)
        # name plate
        draw.rectangle((x1 + 8, y_top + pod_h - 60, x2 - 8, y_top + pod_h - 20),
                       fill=WHITE)
        bbox = draw.textbbox((0, 0), name, font=F_SM)
        tw = bbox[2] - bbox[0]
        cx = x1 + (pod_w - tw) // 2
        draw.text((cx, y_top + pod_h - 50), name, fill=DEEP_BLUE, font=F_SM)
        # score
        s = scores[i]
        if is_winner and progress > 0.45:
            s = s + (delta if correct else -delta)
        s_str = f"${s:,}" if s >= 0 else f"-${abs(s):,}"
        s_color = SCORE_GREEN if s > 0 else (SCORE_RED if s < 0 else WHITE)
        bbox2 = draw.textbbox((0, 0), s_str, font=F_LG)
        tw2 = bbox2[2] - bbox2[0]
        draw.text((x1 + (pod_w - tw2) // 2, y_top + 70), s_str,
                  fill=s_color, font=F_LG)

    # answer caption
    if progress > 0.25:
        draw.rectangle((30, 50, WIDTH - 30, 110), fill=DEEP_BLUE,
                       outline=JEOPARDY_GOLD, width=2)
        draw_centered(draw, names[who], 58, F_SM, PALE_GOLD)
        draw_centered(draw, answer, 78, F_LG, WHITE)

    # bottom ribbon: "CORRECT" or amount
    if progress > 0.55:
        ribbon = "CORRECT!" if correct else "INCORRECT"
        rcol = SCORE_GREEN if correct else SCORE_RED
        draw.rectangle((100, HEIGHT - 70, WIDTH - 100, HEIGHT - 25),
                       fill=rcol)
        sign = "+" if correct else "-"
        label = f"{ribbon}    {sign}${delta:,}"
        if is_dd:
            label = f"DAILY DOUBLE   {sign}${delta:,}"
        draw_centered(draw, label, HEIGHT - 62, F_MD, WHITE)

    return img


def compute_running_scores_at(p):
    """Walk storyboard up to (but not including) this scene; sum deltas to ANTHROPIC."""
    scores = [0, 0, 0]
    for s, e, kind, params in STORYBOARD:
        if params is p:
            return scores
        if kind == "buzz_in":
            who = params.get("who", 0)
            d = params.get("delta", 0)
            ok = params.get("correct", True)
            scores[who] += d if ok else -d
    return scores


def scene_daily_double(fn, tf, p):
    """The iconic Daily Double splash."""
    progress = fn / tf
    img = Image.new('RGB', (WIDTH, HEIGHT), DEEP_BLUE)
    draw = ImageDraw.Draw(img)

    # radiating rays
    cx, cy = WIDTH // 2, HEIGHT // 2
    for ang in range(0, 360, 6):
        rad = math.radians(ang + fn * 2)
        x2 = cx + math.cos(rad) * 600
        y2 = cy + math.sin(rad) * 600
        draw.line([(cx, cy), (x2, y2)], fill=(20, 30, 180), width=4)

    # the words
    if progress > 0.1:
        scale = min(1.0, (progress - 0.1) / 0.4)
        size = int(36 + scale * 60)
        f1 = get_font(size, bold=True)
        bbox = draw.textbbox((0, 0), "DAILY", font=f1)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        y = HEIGHT // 2 - size - 10
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
            draw.text((x + dx, y + dy), "DAILY", fill=BLACK, font=f1)
        draw.text((x, y), "DAILY", fill=JEOPARDY_GOLD, font=f1)
    if progress > 0.35:
        scale = min(1.0, (progress - 0.35) / 0.4)
        size = int(36 + scale * 60)
        f2 = get_font(size, bold=True)
        bbox = draw.textbbox((0, 0), "DOUBLE!", font=f2)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        y = HEIGHT // 2 + 10
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3)]:
            draw.text((x + dx, y + dy), "DOUBLE!", fill=BLACK, font=f2)
        draw.text((x, y), "DOUBLE!", fill=JEOPARDY_GOLD, font=f2)

    # outer border
    draw.rectangle((6, 6, WIDTH - 6, HEIGHT - 6), outline=JEOPARDY_GOLD, width=3)

    return img


def scene_final_jeopardy_card(fn, tf, p):
    """'FINAL JEOPARDY' splash with category."""
    progress = fn / tf
    img = Image.new('RGB', (WIDTH, HEIGHT), DEEP_BLUE)
    draw = ImageDraw.Draw(img)
    # gradient
    arr = np.array(img).astype(float)
    for y in range(HEIGHT):
        f = 1.0 - 0.4 * abs(y - HEIGHT / 2) / HEIGHT
        arr[y] *= f
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)

    draw.rectangle((10, 10, WIDTH - 10, HEIGHT - 10),
                   outline=JEOPARDY_GOLD, width=3)

    if progress < 0.5:
        # title slides in
        x_off = int((1 - min(1.0, progress / 0.4)) * WIDTH)
        draw_centered(draw, "FINAL", HEIGHT // 2 - 90, F_HUGE,
                      JEOPARDY_GOLD)
        draw_centered(draw, "JEOPARDY!", HEIGHT // 2 + 0, F_HUGE,
                      JEOPARDY_GOLD)
        # slide-in mask (simulate with overlay rectangle)
        if x_off > 0:
            draw.rectangle((WIDTH - x_off, 0, WIDTH, HEIGHT),
                           fill=DEEP_BLUE)
    else:
        draw_centered(draw, "FINAL JEOPARDY!", 80, F_XL, JEOPARDY_GOLD)
        # category reveal
        cat_progress = (progress - 0.5) / 0.5
        if cat_progress > 0.1:
            beveled_box(draw, (60, 180, WIDTH - 60, 320),
                        fill=JEOPARDY_BLUE)
            draw_centered(draw, "TODAY'S CATEGORY", 200, F_SM, PALE_GOLD)
            draw_centered(draw, "PARADOXES", 230, F_LG, WHITE)
            draw_centered(draw, "OF 2026", 268, F_LG, WHITE)

    return img


def scene_final_jeopardy_clue(fn, tf, p):
    """The blue clue card. Think music plays."""
    progress = fn / tf
    img = Image.new('RGB', (WIDTH, HEIGHT), JEOPARDY_BLUE)
    draw = ImageDraw.Draw(img)

    arr = np.array(img).astype(float)
    for y in range(HEIGHT):
        f = 1.0 - 0.3 * (y / HEIGHT)
        arr[y] *= f
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)

    draw.rectangle((10, 10, WIDTH - 10, HEIGHT - 10),
                   outline=JEOPARDY_GOLD, width=3)

    draw.text((30, 25), "PARADOXES OF 2026", fill=PALE_GOLD, font=F_SM)
    draw.text((WIDTH - 130, 25), "FINAL", fill=JEOPARDY_GOLD, font=F_SM)

    text = p.get("text", "")
    chars = int(progress * len(text) * 1.4)
    visible = text[:max(0, min(chars, len(text)))]
    if chars < len(text) and (fn % 8) < 4:
        visible += "_"

    draw_text_in_box(draw, visible, (40, 90, WIDTH - 40, HEIGHT - 90),
                     F_LG, WHITE)

    # countdown bar at bottom (think music timer)
    bar_w = int((1 - progress) * (WIDTH - 80))
    draw.rectangle((40, HEIGHT - 50, WIDTH - 40, HEIGHT - 30),
                   outline=JEOPARDY_GOLD, width=2)
    draw.rectangle((40, HEIGHT - 50, 40 + bar_w, HEIGHT - 30),
                   fill=JEOPARDY_GOLD)

    return img


def scene_final_jeopardy_reveal(fn, tf, p):
    """Reveal the answer + final scores."""
    progress = fn / tf
    img = starfield_bg(fn)
    draw = ImageDraw.Draw(img)

    answer = p.get("answer", "")

    # the answer bar
    if progress < 0.6:
        # contestants writing — show three "answer cards"
        names = ["ANTHROPIC", "THE PENTAGON", "TRUTH SOCIAL"]
        guesses = [
            answer,
            "What is... a coincidence?",
            "What is... fake news?",
        ]
        wagers = [10000, 0, 0]
        card_w = 175
        card_h = 230
        gap = (WIDTH - 3 * card_w) // 4
        y_top = 100
        for i in range(3):
            x1 = gap + i * (card_w + gap)
            x2 = x1 + card_w
            beveled_box(draw, (x1, y_top, x2, y_top + card_h),
                        fill=JEOPARDY_BLUE)
            # name
            draw.rectangle((x1 + 8, y_top + 8, x2 - 8, y_top + 36),
                           fill=WHITE)
            bbox = draw.textbbox((0, 0), names[i], font=F_SM)
            tw = bbox[2] - bbox[0]
            draw.text((x1 + (card_w - tw) // 2, y_top + 14),
                      names[i], fill=DEEP_BLUE, font=F_SM)
            # answer (typed reveal)
            chars = int(progress * len(guesses[i]) * 2)
            visible = guesses[i][:max(0, min(chars, len(guesses[i])))]
            draw_text_in_box(draw, visible,
                             (x1 + 6, y_top + 50, x2 - 6, y_top + 150),
                             F_SM, WHITE)
            # wager
            if progress > 0.4:
                draw.rectangle((x1 + 8, y_top + card_h - 50,
                                x2 - 8, y_top + card_h - 10),
                               fill=DEEP_BLUE, outline=JEOPARDY_GOLD)
                wstr = f"${wagers[i]:,}"
                bbox2 = draw.textbbox((0, 0), wstr, font=F_MD)
                tw2 = bbox2[2] - bbox2[0]
                draw.text((x1 + (card_w - tw2) // 2, y_top + card_h - 42),
                          wstr, fill=JEOPARDY_GOLD, font=F_MD)
        draw_centered(draw, "FINAL ANSWERS", 60, F_MD, JEOPARDY_GOLD)
    else:
        # final scoreboard
        draw_centered(draw, "FINAL SCORES", 60, F_LG, JEOPARDY_GOLD)
        # ANTHROPIC wins.
        finals = [("ANTHROPIC", 13000, True),
                  ("THE PENTAGON", -2000, False),
                  ("TRUTH SOCIAL", -5000, False)]
        for i, (n, s, won) in enumerate(finals):
            y = 130 + i * 70
            beveled_box(draw, (50, y, WIDTH - 50, y + 55),
                        fill=JEOPARDY_BLUE)
            draw.text((70, y + 14), n, fill=WHITE, font=F_LG)
            s_str = f"${s:,}" if s >= 0 else f"-${abs(s):,}"
            s_color = SCORE_GREEN if s > 0 else SCORE_RED
            bbox = draw.textbbox((0, 0), s_str, font=F_LG)
            tw = bbox[2] - bbox[0]
            draw.text((WIDTH - 70 - tw, y + 14), s_str,
                      fill=s_color, font=F_LG)
            if won and (fn // 4) % 2 == 0:
                # winner crown / asterisk
                draw.text((20, y + 14), "*", fill=JEOPARDY_GOLD, font=F_LG)

    return img


def scene_end_card(fn, tf, p):
    """Sign-off."""
    progress = fn / tf
    img = starfield_bg(fn)
    draw = ImageDraw.Draw(img)
    if progress < 0.85:
        size = 70
        f = get_font(size, bold=True)
        bbox = draw.textbbox((0, 0), "JEOPARDY!", font=f)
        tw = bbox[2] - bbox[0]
        x = (WIDTH - tw) // 2
        y = HEIGHT // 2 - 60
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            draw.text((x + dx, y + dy), "JEOPARDY!", fill=BLACK, font=f)
        draw.text((x, y), "JEOPARDY!", fill=JEOPARDY_GOLD, font=f)
        draw_centered(draw, "...we'll see you tomorrow.", HEIGHT // 2 + 30, F_MD, WHITE)
        draw_centered(draw, "(if there is one)", HEIGHT // 2 + 65, F_SM, PALE_GOLD)
    # fade
    if progress > 0.6:
        fade = (progress - 0.6) / 0.4
        arr = np.array(img).astype(float)
        arr *= max(0.0, 1.0 - fade)
        img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    return img


# ============================================================
# AUDIO
# ============================================================

def synth_tone(freq, duration_s, amp=0.2, decay=0.0, wave_type="sine"):
    n = int(duration_s * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    if wave_type == "square":
        y = np.sign(np.sin(2 * np.pi * freq * t)) * amp
    elif wave_type == "saw":
        y = (2 * (t * freq - np.floor(t * freq + 0.5))) * amp
    else:
        y = np.sin(2 * np.pi * freq * t) * amp
    if decay > 0:
        y *= np.exp(-t * decay)
    return y


def add_at(audio, sample, start_sample):
    e = min(start_sample + len(sample), len(audio))
    if start_sample >= len(audio):
        return
    audio[start_sample:e] += sample[:e - start_sample]


# Note frequencies (a few semitones we'll need)
NOTES = {
    "G3": 196.00, "A3": 220.00, "B3": 246.94, "C4": 261.63, "D4": 293.66,
    "E4": 329.63, "F4": 349.23, "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99,
    "C3": 130.81,
}


def jeopardy_think_music(duration_s, amp=0.15):
    """The classic 'Think!' theme - simple ostinato C-E-G-E pattern with bell + snap."""
    n = int(duration_s * SAMPLE_RATE)
    out = np.zeros(n)
    bpm = 120
    beat = 60.0 / bpm  # 0.5s
    pattern = ["C5", "E5", "G5", "E5", "C5", "E5", "G5", "E5",
               "C5", "F5", "A4", "F5", "C5", "E5", "G5", "C5"]
    for i in range(int(duration_s / beat) + 1):
        note = pattern[i % len(pattern)]
        f = NOTES[note]
        s = synth_tone(f, beat * 0.9, amp=amp, decay=4.0)
        # bell-like overtone
        s += synth_tone(f * 2, beat * 0.9, amp=amp * 0.3, decay=6.0)
        add_at(out, s, int(i * beat * SAMPLE_RATE))
    # bass line (root every two beats)
    bass = ["C3", "C3", "F3" if False else "C3", "G3"] * 4
    for i in range(int(duration_s / (beat * 2)) + 1):
        note = bass[i % len(bass)]
        f = NOTES.get(note, 130.81)
        s = synth_tone(f, beat * 1.8, amp=amp * 0.6, decay=2.0)
        add_at(out, s, int(i * 2 * beat * SAMPLE_RATE))
    return out


def jeopardy_theme_intro(duration_s, amp=0.2):
    """A short fanfare on a I-IV-V-I-ish progression."""
    n = int(duration_s * SAMPLE_RATE)
    out = np.zeros(n)
    melody = [
        ("E5", 0.3), ("G5", 0.3), ("C5", 0.6),
        ("D5", 0.3), ("G5", 0.3), ("E5", 0.6),
    ]
    t = 0
    for note, dur in melody:
        f = NOTES[note]
        s = synth_tone(f, dur, amp=amp, decay=2.0)
        s += synth_tone(f * 2, dur, amp=amp * 0.4, decay=3.0)
        add_at(out, s, int(t * SAMPLE_RATE))
        t += dur
    return out


def buzzer_ding(duration_s=0.4, amp=0.3):
    n = int(duration_s * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    y = np.sin(2 * np.pi * 880 * t) * amp
    y += np.sin(2 * np.pi * 1320 * t) * amp * 0.5
    y *= np.exp(-t * 5)
    return y


def buzzer_wrong(duration_s=0.4, amp=0.3):
    n = int(duration_s * SAMPLE_RATE)
    t = np.arange(n) / SAMPLE_RATE
    y = np.sin(2 * np.pi * 200 * t) * amp
    y *= np.exp(-t * 3)
    return y


def daily_double_sting(duration_s=2.5, amp=0.25):
    NOTES.setdefault("C6", 1046.5)
    n = int(duration_s * SAMPLE_RATE)
    out = np.zeros(n)
    pattern = [
        ("C5", 0.15), ("E5", 0.15), ("G5", 0.15),
        ("C5", 0.15), ("E5", 0.15), ("G5", 0.15),
        ("C6", 0.5),
    ]
    t = 0
    for note, dur in pattern:
        f = NOTES[note]
        s = synth_tone(f, dur, amp=amp, decay=3.0)
        s += synth_tone(f * 2, dur, amp=amp * 0.4, decay=4.0)
        add_at(out, s, int(t * SAMPLE_RATE))
        t += dur
    return out


def applause(duration_s, amp=0.1):
    n = int(duration_s * SAMPLE_RATE)
    noise = np.random.randn(n) * amp
    # smooth a bit
    for i in range(1, n):
        noise[i] = noise[i - 1] * 0.6 + noise[i] * 0.4
    return noise


def generate_audio():
    total_samples = SAMPLE_RATE * DURATION
    audio = np.zeros(total_samples, dtype=np.float64)

    for start_sec, end_sec, kind, params in STORYBOARD:
        s = int(start_sec * SAMPLE_RATE)
        n = int((end_sec - start_sec) * SAMPLE_RATE)
        if kind == "theme_intro":
            add_at(audio, jeopardy_theme_intro(end_sec - start_sec, amp=0.25), s)
            add_at(audio, applause(end_sec - start_sec, amp=0.04), s)
        elif kind == "host_intro":
            add_at(audio, applause(end_sec - start_sec, amp=0.05), s)
            # soft bed tone
            t = np.arange(n) / SAMPLE_RATE
            bed = np.sin(2 * np.pi * 220 * t) * 0.04
            add_at(audio, bed, s)
        elif kind == "game_board":
            # a few "reveal" beeps as cells appear
            for i in range(6):
                add_at(audio, synth_tone(523 + i * 30, 0.08, amp=0.1, decay=8.0),
                       s + int(i * 0.4 * SAMPLE_RATE))
            t = np.arange(n) / SAMPLE_RATE
            bed = np.sin(2 * np.pi * 110 * t) * 0.04
            add_at(audio, bed, s)
        elif kind == "pick_clue":
            # short uptick
            add_at(audio, synth_tone(660, 0.1, amp=0.12, decay=8.0), s)
        elif kind in ("clue_card", "clue_card_dd"):
            # subtle bed + buzzer at end
            t = np.arange(n) / SAMPLE_RATE
            bed = np.sin(2 * np.pi * 130 * t) * 0.05
            add_at(audio, bed, s)
            # typewriter clicks
            text = params.get("text", "")
            char_dur = (end_sec - start_sec) / max(1, len(text))
            for i in range(min(len(text), int(n / SAMPLE_RATE / max(0.001, char_dur)))):
                if random.random() < 0.6:
                    click = synth_tone(2000 + random.randint(-200, 200),
                                       0.01, amp=0.05, decay=80.0)
                    add_at(audio, click, s + int(i * char_dur * SAMPLE_RATE))
            # buzzer at end
            add_at(audio, buzzer_ding(),
                   s + n - int(0.4 * SAMPLE_RATE))
        elif kind == "buzz_in":
            # ding at start, then "correct" affirmation
            add_at(audio, buzzer_ding(0.3, amp=0.35), s)
            if params.get("correct", True):
                # 3-note affirmative
                for i, note in enumerate(["C5", "E5", "G5"]):
                    add_at(audio, synth_tone(NOTES[note], 0.12, amp=0.15, decay=4.0),
                           s + int((0.4 + i * 0.12) * SAMPLE_RATE))
                add_at(audio, applause(end_sec - start_sec - 0.6, amp=0.05),
                       s + int(0.7 * SAMPLE_RATE))
            else:
                add_at(audio, buzzer_wrong(0.5, amp=0.3), s + int(0.4 * SAMPLE_RATE))
        elif kind == "daily_double":
            add_at(audio, daily_double_sting(end_sec - start_sec, amp=0.3), s)
            add_at(audio, applause(end_sec - start_sec, amp=0.06), s)
        elif kind == "final_jeopardy_card":
            # dramatic chord
            for note in ["C4", "E4", "G4", "C5"]:
                add_at(audio, synth_tone(NOTES[note], end_sec - start_sec,
                                         amp=0.1, decay=0.8), s)
        elif kind == "final_jeopardy_clue":
            # the iconic think music
            add_at(audio, jeopardy_think_music(end_sec - start_sec, amp=0.18), s)
        elif kind == "final_jeopardy_reveal":
            # ending sting
            for i, note in enumerate(["C5", "G4", "C5"]):
                add_at(audio, synth_tone(NOTES[note], 0.4, amp=0.18, decay=2.0),
                       s + int(i * 0.3 * SAMPLE_RATE))
            add_at(audio, applause(end_sec - start_sec - 1.0, amp=0.07),
                   s + int(1.0 * SAMPLE_RATE))
        elif kind == "end_card":
            # outro fanfare
            add_at(audio, jeopardy_theme_intro(end_sec - start_sec, amp=0.2), s)

    # master
    audio = np.tanh(audio * 1.2) * 0.85
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.85
    audio_16 = (audio * 32767).astype(np.int16)
    with wave.open(str(AUDIO_FILE), 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(audio_16.tobytes())
    print(f"Audio: {AUDIO_FILE}")


# ============================================================
# DISPATCH
# ============================================================

SCENES = {
    "theme_intro": scene_theme_intro,
    "host_intro": scene_host_intro,
    "game_board": scene_game_board,
    "pick_clue": scene_pick_clue,
    "clue_card": scene_clue_card,
    "clue_card_dd": scene_clue_card_dd,
    "buzz_in": scene_buzz_in,
    "daily_double": scene_daily_double,
    "final_jeopardy_card": scene_final_jeopardy_card,
    "final_jeopardy_clue": scene_final_jeopardy_clue,
    "final_jeopardy_reveal": scene_final_jeopardy_reveal,
    "end_card": scene_end_card,
}


def get_scene_for_time(time_sec):
    for s, e, k, p in STORYBOARD:
        if s <= time_sec < e:
            return s, e, k, p
    return STORYBOARD[-1]


def generate_frame(global_frame_num):
    time_sec = global_frame_num / FPS
    s, e, kind, params = get_scene_for_time(time_sec)
    scene_dur = e - s
    scene_time = time_sec - s
    scene_frame = int(scene_time * FPS)
    total_scene_frames = max(1, int(scene_dur * FPS))
    fn = SCENES.get(kind)
    if fn is None:
        return Image.new('RGB', (WIDTH, HEIGHT), DEEP_BLUE)
    return fn(scene_frame, total_scene_frames, params)


def main():
    print("=" * 60)
    print("  CLAUDE 2026: A JEOPARDY! EPISODE")
    print("=" * 60)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nGenerating {TOTAL_FRAMES} frames at {FPS}fps ({DURATION}s)...")
    for i in range(TOTAL_FRAMES):
        img = generate_frame(i)
        img.save(FRAMES_DIR / f"frame_{i:05d}.png")
        if (i + 1) % FPS == 0:
            print(f"  [{(i+1)//FPS}/{DURATION}s]  {i+1}/{TOTAL_FRAMES}")
    print("\nGenerating audio...")
    generate_audio()
    print("\nRendering with ffmpeg...")
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", str(FRAMES_DIR / "frame_%05d.png"),
        "-i", str(AUDIO_FILE),
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(OUTPUT_FILE),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stderr)
        return False
    import shutil
    shutil.rmtree(FRAMES_DIR)
    AUDIO_FILE.unlink(missing_ok=True)
    sz = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    print(f"\n{'=' * 60}")
    print(f"  RENDERED: {OUTPUT_FILE}")
    print(f"  SIZE: {sz:.1f} MB | DURATION: {DURATION}s @ {FPS}fps")
    print(f"{'=' * 60}")
    return True


if __name__ == "__main__":
    main()
