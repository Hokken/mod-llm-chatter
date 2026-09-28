#!/usr/bin/env python3
"""Print a real group_idle_conv speaker block from live data.

Builds the prompt exactly as the idle conversation handler
does, against the running database, so the gear lines can be
inspected without waiting for a player to log in.

  docker exec -w /app ac-llm-chatter-bridge \
      python tests/manual_gear_prompt_check.py Veliana Erodora
"""

import os
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import mysql.connector  # noqa: E402

from chatter_group import (  # noqa: E402
    build_idle_conversation_prompt,
)
from chatter_shared import (  # noqa: E402
    attach_speaker_gear,
    get_class_name,
    get_race_name,
)


def main() -> int:
    names = sys.argv[1:] or ['Veliana', 'Erodora']

    db = mysql.connector.connect(
        host=os.environ.get('CHATTER_DB_HOST', 'ac-database'),
        user=os.environ.get('CHATTER_DB_USER', 'root'),
        password=os.environ.get('CHATTER_DB_PASS', 'password'),
        database=os.environ.get(
            'CHATTER_DB_NAME', 'acore_characters',
        ),
    )
    cursor = db.cursor(dictionary=True)

    bots = []
    traits_map = {}
    for name in names:
        cursor.execute(
            "SELECT guid, class, race, level "
            "FROM characters WHERE name = %s",
            (name,),
        )
        row = cursor.fetchone()
        if not row:
            print(f"no such character: {name}")
            return 1
        bots.append({
            'guid': row['guid'],
            'name': name,
            'class': get_class_name(row['class']),
            'race': get_race_name(row['race']),
            'level': row['level'],
        })
        traits_map[name] = ['curious', 'wary', 'dry']

    attach_speaker_gear(db, bots, None)

    prompt = build_idle_conversation_prompt(
        bots, traits_map, 'roleplay',
        topic='noticing the time of day',
        player_name='Melindra',
    )

    print('=== gear resolved per speaker ===')
    for bot in bots:
        print(f"  {bot['name']}: {bot.get('gear_third')!r}")

    print()
    print('=== speaker block as the model sees it ===')
    for line in prompt.split('\n'):
        if (
            ' is a level ' in line
            or ' wields ' in line
            or 'pet is' in line
            or line.startswith('Speakers:')
        ):
            print(f"  {line}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
