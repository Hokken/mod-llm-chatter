#!/usr/bin/env python3
"""Generate talent_data.json from the WotLK 3.3.5a client DBC files.

acore_world.talent_dbc is empty by design (the core loads Talent.dbc from
the client data), so the bridge maps character_talent spells to talent
trees with this file instead.

Talent names come from spell_names.json (rank 1 spell). From the module
root, for example:
  docker exec ac-worldserver cat /azerothcore/env/dist/data/dbc/Talent.dbc \\
    > /tmp/Talent.dbc
  docker exec ac-worldserver cat /azerothcore/env/dist/data/dbc/TalentTab.dbc \\
    > /tmp/TalentTab.dbc
  python3 tools/generate_talent_data.py /tmp/Talent.dbc /tmp/TalentTab.dbc \\
    > tools/talent_data.json
"""

import argparse
import json
import struct
import sys
from typing import Dict, List, Tuple

# Talent.dbc: ID, TabID, TierID, ColumnIndex, SpellRank[9], ...
TALENT_FIELDS = 23
# TalentTab.dbc: ID, Name_Lang[16], mask, SpellIconID, RaceMask, ClassMask,
# PetTalentMask, OrderIndex, BackgroundFile
TALENT_TAB_FIELDS = 24


def read_dbc(path: str, fields: int) -> Tuple[List[tuple], bytes]:
    with open(path, 'rb') as handle:
        data = handle.read()
    magic, count, field_count, record_size, _ = struct.unpack(
        '<4s4I', data[:20])
    if magic != b'WDBC' or field_count != fields:
        raise ValueError(f"{path}: unexpected DBC layout "
                         f"({magic!r}, {field_count} fields)")
    records = [
        struct.unpack(f'<{fields}I',
                      data[20 + i * record_size:20 + (i + 1) * record_size])
        for i in range(count)
    ]
    return records, data[20 + count * record_size:]


def dbc_string(strings: bytes, offset: int) -> str:
    end = strings.index(b'\0', offset)
    return strings[offset:end].decode('utf-8', 'replace')


def load_names(spell_ids: List[int]) -> Dict[int, str]:
    from spell_names import SPELL_NAMES
    # spell_names.json stores some apostrophes as \\'
    return {
        spell_id: SPELL_NAMES[spell_id].replace('\\', '')
        for spell_id in spell_ids if SPELL_NAMES.get(spell_id)
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('talent_dbc')
    parser.add_argument('talent_tab_dbc')
    args = parser.parse_args()

    tab_rows, tab_strings = read_dbc(args.talent_tab_dbc, TALENT_TAB_FIELDS)
    tabs = {
        str(row[0]): {
            'name': dbc_string(tab_strings, row[1]),
            'class_mask': row[20],
            'order': row[22],
        }
        for row in tab_rows
    }

    talent_rows, _ = read_dbc(args.talent_dbc, TALENT_FIELDS)
    names = load_names([row[4] for row in talent_rows if row[4]])
    spells = {}
    missing = 0
    for row in talent_rows:
        talent_id, tab_id, tier, column = row[0:4]
        ranks = row[4:13]
        if not ranks[0]:
            continue
        name = names.get(ranks[0], '')
        if not name:
            missing += 1
        for rank, spell_id in enumerate(ranks, 1):
            if spell_id:
                spells[str(spell_id)] = [
                    talent_id, tab_id, rank, tier, column, name,
                ]

    json.dump({'tabs': tabs, 'spells': spells}, sys.stdout,
              ensure_ascii=False, indent=0, sort_keys=True)
    sys.stdout.write('\n')
    print(f"{len(tabs)} tabs, {len(spells)} talent spells, "
          f"{missing} talents without a name", file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
