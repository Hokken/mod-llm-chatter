"""Screenshot Vision Agent — host-side capture and analysis.

Runs on the Windows host (not in Docker). Periodically captures the
WoW game window, sends it to a vision LLM for structured environmental
analysis, and inserts the result into llm_chatter_events so the bridge
can generate an in-character bot comment.

Usage:
    python screenshot_agent.py --config path/to/mod_llm_chatter.conf

Requirements (host-side):
    pip install mss Pillow anthropic mysql-connector-python pywin32
"""

import argparse
import base64
import ctypes
import ctypes.wintypes
import io
import json
import logging
import os
import random
import re
import sys
import time

import mysql.connector
from PIL import Image

log = logging.getLogger("screenshot_agent")

# -----------------------------------------------------------
# Vision prompt — Stage 1 (pure extraction, no personality)
# -----------------------------------------------------------

VISION_SYSTEM = (
    "You are analyzing a World of Warcraft screenshot. "
    "Look PAST all UI elements and text overlays — "
    "focus ONLY on the 3D game world visible behind "
    "them. Describe the environment, landscape, and "
    "atmosphere — what the world itself looks like.\n\n"
    "DESCRIBE (both outdoors AND indoors):\n"
    "- Outdoor: terrain, vegetation, water bodies, "
    "paths, bridges, ruins, towers, caves, banners\n"
    "- Indoor: room layout, furniture, barrels, crates, "
    "shelves, fireplaces, chandeliers, stairs, doorways, "
    "windows, decorations, building materials\n"
    "- Architecture: buildings, arches, columns, walls, "
    "roofs, wooden beams, stone work, forges, altars\n"
    "- Atmosphere: lighting, mood, color tones, shadows, "
    "weather, fog, rain, snow, time of day\n"
    "- Non-humanoid creatures ONLY: animals, beasts, "
    "spiders, wolves, birds, undead monsters, demons, "
    "elementals. Do NOT mention any humanoid figures\n\n"
    "IGNORE (do not describe, but do NOT skip the scene "
    "just because they are present):\n"
    "- ALL humanoid figures — player characters, NPCs, "
    "guards, vendors, other players, party members. "
    "Humanoids do NOT make a scene uninteresting. "
    "Describe the world around and behind them\n"
    "- ALL UI elements: health bars, mana bars, action "
    "bars, minimap, chat window, nameplates, buff/debuff "
    "icons, tooltips, quest tracker, bag slots, menus\n"
    "- ALL text on screen — chat messages, zone names, "
    "quest text, NPC dialogue, damage numbers, floating "
    "combat text, discovery banners, tooltips, item "
    "names, player names, guild names. Do NOT read or "
    "reference any text visible in the image\n"
    "- Cursor or selection indicators\n\n"
    "Return ONLY valid JSON with these fields:\n"
    "{\n"
    '  "landmark_type": "one of: castle, ruins, bridge, '
    "tower, cave, waterfall, lake, river, camp, village, "
    "city, ship, gate, statue, shrine, none\",\n"
    '  "weather": "one of: clear, cloudy, foggy, rainy, '
    "snowy, stormy, none\",\n"
    '  "time_of_day": "one of: dawn, day, dusk, night, '
    "unknown\",\n"
    '  "biome": "one of: forest, tundra, desert, swamp, '
    "mountain, coastal, plains, volcanic, underground, "
    "urban, none\",\n"
    '  "atmosphere": "brief mood/lighting description '
    "or null\",\n"
    '  "environment": "brief terrain/landmark description '
    "or null\",\n"
    '  "creatures": "brief NON-HUMANOID creature '
    "description or null\",\n"
    '  "skip_reason": "if ALL other fields are null, '
    "explain why in a few words. Otherwise null\"\n"
    "}\n"
    "If the scene is a loading screen, character select, "
    "or entirely obscured by UI, return all null/none.\n"
    "Almost every scene has something worth describing: "
    "architecture, interiors, lighting, vegetation, "
    "weather, terrain. Ignore the humanoids but describe "
    "the world behind and around them. Only return all "
    "null/none if you truly cannot see any game world."
)

# -----------------------------------------------------------
# Config parsing (reuse chatter pattern)
# -----------------------------------------------------------


def parse_config(config_path: str) -> dict:
    """Parse WoW-style Key = Value config file."""
    cfg = {}
    with open(config_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, _, val = line.partition('=')
            cfg[key.strip()] = val.strip()
    return cfg


def load_screenshot_config(raw: dict) -> dict:
    """Extract screenshot-specific config with defaults."""
    return {
        'enable': raw.get(
            'LLMChatter.Screenshot.Enable', '0') == '1',
        'interval_min_seconds': int(raw.get(
            'LLMChatter.Screenshot.IntervalMinSeconds',
            '300')),
        'interval_max_seconds': int(raw.get(
            'LLMChatter.Screenshot.IntervalMaxSeconds',
            '600')),
        'chance': int(raw.get(
            'LLMChatter.Screenshot.Chance', '30')),
        'vision_provider': raw.get(
            'LLMChatter.Screenshot.VisionProvider',
            'openai'),
        'vision_model': raw.get(
            'LLMChatter.Screenshot.VisionModel',
            'gpt-4o-mini'),
        'bound_account_id': int(raw.get(
            'LLMChatter.Screenshot.BoundAccountId', '0')),
        'max_width_px': int(raw.get(
            'LLMChatter.Screenshot.MaxWidthPx', '640')),
        'jpeg_quality': int(raw.get(
            'LLMChatter.Screenshot.JpegQuality', '75')),
        'anthropic_api_key': raw.get(
            'LLMChatter.Anthropic.ApiKey', ''),
        'openai_api_key': raw.get(
            'LLMChatter.OpenAI.ApiKey', ''),
        # Host-side override: Database.Host is typically a
        # Docker-internal hostname (e.g. ac-database) which
        # the Windows host can't resolve. Screenshot.DBHost
        # lets the agent use 127.0.0.1 without changing the
        # shared bridge config.
        'db_host': raw.get(
            'LLMChatter.Screenshot.DBHost',
            raw.get('LLMChatter.Database.Host',
                    '127.0.0.1')),
        'db_port': int(raw.get(
            'LLMChatter.Database.Port', '3306')),
        'db_user': raw.get(
            'LLMChatter.Database.User', 'root'),
        'db_pass': raw.get(
            'LLMChatter.Database.Password', 'password'),
        'db_name': raw.get(
            'LLMChatter.Database.Name',
            'acore_characters'),
    }


# -----------------------------------------------------------
# Window capture
# -----------------------------------------------------------


def is_wow_foreground() -> bool:
    """Check if WoW is the active foreground window."""
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        return "World of Warcraft" in title
    except Exception:
        return False


def capture_wow_window() -> 'Image.Image | None':
    """Capture the WoW game client area."""
    try:
        import mss
        import win32gui
        hwnd = win32gui.FindWindow(
            None, "World of Warcraft")
        if not hwnd:
            return None

        rect = win32gui.GetClientRect(hwnd)
        point = ctypes.wintypes.POINT(0, 0)
        ctypes.windll.user32.ClientToScreen(
            hwnd, ctypes.byref(point))
        left, top = point.x, point.y
        width, height = rect[2], rect[3]
        if width <= 0 or height <= 0:
            return None
        with mss.mss() as sct:
            region = {
                "left": left, "top": top,
                "width": width, "height": height,
            }
            raw = sct.grab(region)
            return Image.frombytes(
                "RGB", raw.size, raw.bgra,
                "raw", "BGRX")
    except Exception as e:
        log.warning("WoW window capture failed: %s", e)
        return None


# -----------------------------------------------------------
# Image compression
# -----------------------------------------------------------


def crop_screenshot(img: 'Image.Image') -> 'Image.Image':
    """Light crop to reduce UI clutter while keeping
    most of the game world visible. Removes bottom 15%
    (action bars) and 5% from each side."""
    w, h = img.size
    left = int(w * 0.05)
    right = int(w * 0.95)
    top = 0
    bottom = int(h * 0.85)
    return img.crop((left, top, right, bottom))


def compress_screenshot(
    img: 'Image.Image',
    max_width: int = 640,
    jpeg_quality: int = 75,
) -> bytes:
    """Resize and JPEG-compress screenshot for API upload."""
    if img.width > max_width:
        ratio = max_width / img.width
        new_h = int(img.height * ratio)
        img = img.resize(
            (max_width, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(
        buf, format="JPEG",
        quality=jpeg_quality, optimize=True)
    return buf.getvalue()


# -----------------------------------------------------------
# Vision analysis — Stage 1
# -----------------------------------------------------------


def _call_anthropic(
    jpeg_b64: str, client, model: str,
) -> 'str | None':
    resp = client.messages.create(
        model=model,
        max_tokens=300,
        system=VISION_SYSTEM,
        messages=[{
            "role": "user",
            "content": [{
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": jpeg_b64,
                },
            }, {
                "type": "text",
                "text": "What do you see in this scene?",
            }],
        }],
    )
    return resp.content[0].text.strip()


def _call_openai(
    jpeg_b64: str, client, model: str,
) -> 'str | None':
    resp = client.chat.completions.create(
        model=model,
        max_tokens=300,
        messages=[{
            "role": "system",
            "content": VISION_SYSTEM,
        }, {
            "role": "user",
            "content": [{
                "type": "image_url",
                "image_url": {
                    "url": (
                        "data:image/jpeg;base64,"
                        + jpeg_b64
                    ),
                },
            }, {
                "type": "text",
                "text": "What do you see in this scene?",
            }],
        }],
    )
    return resp.choices[0].message.content.strip()


def analyze_screenshot(
    jpeg_bytes: bytes,
    client,
    model: str,
    provider: str = 'openai',
) -> 'dict | None':
    """Send screenshot to vision LLM, return structured
    description or None if uninteresting / error."""
    b64 = base64.standard_b64encode(jpeg_bytes).decode()

    try:
        if provider == 'anthropic':
            raw = _call_anthropic(b64, client, model)
        else:
            raw = _call_openai(b64, client, model)
    except Exception as e:
        log.error("Vision API call failed: %s", e)
        return None

    if not raw:
        return None

    # Robust JSON extraction — handle markdown fences
    match = re.search(r'\{[^{}]*\}', raw, re.DOTALL)
    if not match:
        log.warning("No JSON found in vision response")
        return None
    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        log.warning("JSON parse failed for vision response")
        return None

    desc_fields = ['atmosphere', 'environment', 'creatures']
    tag_fields = ['landmark_type', 'biome', 'weather']
    has_desc = any(
        _is_value_present(data.get(k))
        for k in desc_fields
    )
    has_tag = any(
        _is_value_present(data.get(k))
        for k in tag_fields
    )
    if not has_desc and not has_tag:
        reason = data.get('skip_reason', 'no reason given')
        log.info("Vision: skipped — %s", reason)
        return None

    return data


# -----------------------------------------------------------
# Dedup — canonical tag comparison
# -----------------------------------------------------------

def _is_value_present(val) -> bool:
    """True if a vision JSON value is meaningful."""
    return bool(val) and str(val).lower() not in (
        'null', 'none', '')


_last_tags: 'tuple | None' = None


def _extract_tags(desc: dict) -> tuple:
    """Extract canonical dedup key from vision output."""
    return (
        str(desc.get('landmark_type') or 'none').lower(),
        str(desc.get('biome') or 'none').lower(),
        str(desc.get('weather') or 'none').lower(),
        str(desc.get('time_of_day') or 'unknown').lower(),
        _is_value_present(desc.get('creatures')),
    )


def is_duplicate(new_desc: dict) -> bool:
    """Check if canonical tags match the last observation."""
    global _last_tags
    new_tags = _extract_tags(new_desc)
    if _last_tags is None:
        return False
    return new_tags == _last_tags


def update_dedup_cache(desc: dict) -> None:
    """Call after successful queue insert."""
    global _last_tags
    _last_tags = _extract_tags(desc)


# -----------------------------------------------------------
# Database helpers
# -----------------------------------------------------------


def get_db_connection(config: dict):
    """Open a MySQL connection to acore_characters."""
    return mysql.connector.connect(
        host=config['db_host'],
        port=config['db_port'],
        user=config['db_user'],
        password=config['db_pass'],
        database=config['db_name'],
    )


def get_bound_player_group(
    db, account_id: int,
) -> 'dict | None':
    """Find the group for a specific player account."""
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT gm.guid AS group_id,
                   c.zone, c.map
            FROM characters c
            JOIN group_member gm
                ON gm.memberGuid = c.guid
            WHERE c.account = %s
              AND c.online = 1
            LIMIT 1
        """, (account_id,))
        row = cursor.fetchone()
    finally:
        cursor.close()

    if not row:
        return None

    # Pick a random bot from the group as speaker
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT bot_guid, bot_name
            FROM llm_group_bot_traits
            WHERE group_id = %s
            ORDER BY RAND()
            LIMIT 1
        """, (row['group_id'],))
        bot = cursor.fetchone()
    finally:
        cursor.close()

    if not bot:
        return None

    row['bot_guid'] = bot['bot_guid']
    row['bot_name'] = bot['bot_name']
    return row


def get_active_group_fallback(db) -> 'dict | None':
    """Fallback: find first group with bots and a real
    player. Used when BoundAccountId is not set."""
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.group_id, t.bot_guid, t.bot_name,
                   c.zone, c.map
            FROM llm_group_bot_traits t
            JOIN group_member gm
                ON gm.guid = t.group_id
            JOIN characters c
                ON c.guid = gm.memberGuid
                AND c.account != 0
                AND c.online = 1
            ORDER BY RAND()
            LIMIT 1
        """)
        row = cursor.fetchone()
    finally:
        cursor.close()
    return row


def queue_screenshot_event(
    db,
    group_info: dict,
    description: dict,
) -> None:
    """Insert screenshot observation into events table.
    Zone name is resolved by the bridge handler, not here.
    """
    extra = json.dumps({
        "bot_guid":      group_info['bot_guid'],
        "bot_name":      group_info['bot_name'],
        "group_id":      group_info['group_id'],
        "landmark_type": str(
            description.get('landmark_type') or 'none'),
        "weather":       str(
            description.get('weather') or 'none'),
        "time_of_day":   str(
            description.get('time_of_day') or 'unknown'),
        "biome":         str(
            description.get('biome') or 'none'),
        "atmosphere":    str(
            description.get('atmosphere') or ''),
        "environment":   str(
            description.get('environment') or ''),
        "creatures":     str(
            description.get('creatures') or ''),
    })
    cursor = db.cursor()
    try:
        cursor.execute("""
            INSERT INTO llm_chatter_events
                (event_type, event_scope, zone_id, map_id,
                 priority, subject_guid, subject_name,
                 extra_data, status, react_after,
                 expires_at)
            VALUES
                ('bot_group_screenshot_observation',
                 'player', %s, %s, 10, %s, %s, %s,
                 'pending',
                 DATE_ADD(NOW(), INTERVAL 2 SECOND),
                 DATE_ADD(NOW(), INTERVAL 120 SECOND))
        """, (
            group_info['zone'],
            group_info['map'],
            group_info['bot_guid'],
            group_info['bot_name'],
            extra,
        ))
        db.commit()
    finally:
        cursor.close()


# -----------------------------------------------------------
# Main loop
# -----------------------------------------------------------


def _do_capture_cycle(
    config: dict,
    vision_client: 'anthropic.Anthropic',
) -> None:
    """Single capture-analyze-queue cycle."""
    if not is_wow_foreground():
        return

    # Check for active group BEFORE capturing/calling
    # the vision API — no point spending money if
    # there's nobody to deliver the observation to.
    db = get_db_connection(config)
    try:
        account_id = config.get('bound_account_id', 0)
        if account_id:
            group_info = get_bound_player_group(
                db, account_id)
        else:
            group_info = get_active_group_fallback(db)
    finally:
        db.close()

    if group_info is None:
        log.info("No active group with bots, skipping")
        return

    # -- Capture and analyze --
    img = capture_wow_window()
    if img is None:
        return

    try:
        cropped = crop_screenshot(img)
        jpeg_bytes = compress_screenshot(
            cropped,
            max_width=config['max_width_px'],
            jpeg_quality=config['jpeg_quality'],
        )
    finally:
        img.close()
    log.info(
        "Captured screenshot: %d bytes",
        len(jpeg_bytes),
    )

    # Save screenshot for inspection
    from datetime import datetime
    logs_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'logs', 'screenshots',
    )
    os.makedirs(logs_dir, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    debug_path = os.path.join(
        logs_dir, f'screenshot_{ts}.jpg')
    with open(debug_path, 'wb') as f:
        f.write(jpeg_bytes)

    description = analyze_screenshot(
        jpeg_bytes,
        vision_client,
        config['vision_model'],
        provider=config['vision_provider'],
    )
    if description is None:
        return

    if is_duplicate(description):
        log.info("Vision: duplicate scene, skipping")
        return

    log.info(
        "Vision: landmark=%s biome=%s weather=%s",
        description.get('landmark_type', 'none'),
        description.get('biome', 'none'),
        description.get('weather', 'none'),
    )

    # -- Queue the event --
    db = get_db_connection(config)
    try:
        queue_screenshot_event(
            db, group_info, description)
        update_dedup_cache(description)
        log.info(
            "Queued observation: %s (zone_id=%s)",
            group_info['bot_name'],
            group_info['zone'],
        )
    finally:
        db.close()


def _create_vision_client(config: dict):
    """Create the vision API client based on provider."""
    provider = config['vision_provider']
    if provider == 'anthropic':
        import anthropic
        return anthropic.Anthropic(
            api_key=config['anthropic_api_key'])
    else:
        import openai
        return openai.OpenAI(
            api_key=config['openai_api_key'])


def run_agent(config: dict) -> None:
    """Main agent loop — runs indefinitely."""
    vision_client = _create_vision_client(config)
    log.info(
        "Screenshot agent started "
        "(interval=%d-%ds, chance=%d%%)",
        config['interval_min_seconds'],
        config['interval_max_seconds'],
        config['chance'],
    )
    while True:
        interval = random.randint(
            config['interval_min_seconds'],
            config['interval_max_seconds'],
        )
        time.sleep(interval)

        if random.randint(1, 100) > config['chance']:
            continue

        try:
            _do_capture_cycle(config, vision_client)
        except Exception as e:
            log.error("Capture cycle failed: %s", e)
            continue


def main():
    parser = argparse.ArgumentParser(
        description='Screenshot Vision Agent',
    )
    parser.add_argument(
        '--config', required=True,
        help='Path to mod_llm_chatter.conf',
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format=(
            '%(asctime)s %(levelname)s '
            '[%(name)s] %(message)s'
        ),
    )

    raw = parse_config(args.config)
    config = load_screenshot_config(raw)

    if not config['enable']:
        log.error(
            "LLMChatter.Screenshot.Enable is not set to 1")
        sys.exit(1)

    provider = config['vision_provider']
    if provider == 'anthropic':
        if not config['anthropic_api_key']:
            log.error(
                "LLMChatter.Anthropic.ApiKey not set")
            sys.exit(1)
    else:
        if not config['openai_api_key']:
            log.error(
                "LLMChatter.OpenAI.ApiKey not set")
            sys.exit(1)

    run_agent(config)


if __name__ == '__main__':
    main()
