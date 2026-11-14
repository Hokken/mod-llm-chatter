#!/usr/bin/env python3
"""Group awareness for grouped bots speaking outside party chat
(issue #94).

Covers the per-speaker presence block, the strict member_since
boundary on every private context, raid and bot-only omissions,
delivered-only party lines, co-location wording, the activity ring
(occurrence time, ordering, tombstones, bounds, concurrency) and the
proximity prompt wiring (unchanged prompts without a grouped speaker).

Run directly from the module root:
  python tools/tests/test_party_presence.py
"""

import sys
import threading
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_persona_coherence  # noqa: E402,F401  stubs + path

import chatter_party_presence as presence  # noqa: E402
import chatter_proximity as prox  # noqa: E402

JOINED = 1_000_000
NOW = JOINED + 300


class Cursor:
    def __init__(self, db):
        self.db = db
        self.rows = []

    def execute(self, query, params=None):
        params = tuple(params or ())
        self.db.queries.append((query, params))
        if 'FROM llm_chatter_messages' in query:
            self.rows = self._ordered(query, params, self.db.bot_rows,
                                      'delivered_at')
        elif 'FROM llm_group_chat_history' in query:
            self.rows = self._ordered(query, params,
                                      self.db.player_rows, 'created_at')
        elif 'FROM llm_chatter_events' in query:
            self.rows = [{'ts': self.db.event_ts.get(params[0])}]
        else:
            self.rows = []

    @staticmethod
    def _ordered(query, params, rows, time_column):
        """Honour the query's ORDER BY and LIMIT like MySQL would:
        by the time column (then id) when it orders by time, else by
        id only."""
        if f'ORDER BY {time_column} DESC, id DESC' in query:
            key = lambda r: (r.get('ts', 0), r.get('id', 0))  # noqa: E731
        else:
            key = lambda r: r.get('id', 0)  # noqa: E731
        ordered = sorted(rows, key=key, reverse=True)
        return ordered[:int(params[-1])]

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def close(self):
        pass


class DB:
    def __init__(self, bot_rows=(), player_rows=(), event_ts=None):
        self.queries = []
        self.bot_rows = list(bot_rows)
        self.player_rows = list(player_rows)
        self.event_ts = dict(event_ts or {})

    def cursor(self, *args, **kwargs):
        return Cursor(self)

    def commit(self):
        pass

    def tables(self):
        found = []
        for query, _ in self.queries:
            for table in ('llm_chatter_messages',
                          'llm_group_chat_history'):
                if table in query:
                    found.append(table)
        return found


def group(group_id=5, *, raid=False, real=True, since=JOINED,
          members=None, area='Thunder Bluff'):
    return {
        'group_id': group_id, 'is_raid': raid, 'subgroup': 0,
        'member_since': since, 'with_real_player': real,
        'self': {'zone_name': 'Mulgore', 'area_name': area,
                 'is_instance': False, 'map_name': ''},
        'members': members if members is not None else [
            {'name': 'Rob', 'is_player': True, 'near': True,
             'same_zone': True},
            {'name': 'Vex', 'is_player': False, 'near': False,
             'same_zone': True},
            {'name': 'Kael', 'is_player': False, 'near': False,
             'same_zone': False},
        ],
    }


def bot(name='Thalia', grp=None):
    speaker = {'name': name, 'is_npc': False, 'bot_guid': 11}
    if grp is not None:
        speaker['group'] = grp
    return speaker


NPC = {'name': 'Innkeeper Allison', 'is_npc': True, 'role': 'innkeeper'}


def lines(db, speakers, config=None, player='Rob'):
    with patch.object(presence.time, 'time', return_value=NOW):
        return presence.build_presence_lines(
            db, speakers, config or {}, 'open /say',
            player_name=player)


def feed(db, event_id, event_type, extra, group_id=5, config=None):
    with patch.object(presence.time, 'time', return_value=NOW):
        presence.note_group_event(
            db, {'id': event_id, 'event_type': event_type,
                 '_group_id': group_id},
            extra, config or {})


# ------------------------------------------------------------
# Block presence
# ------------------------------------------------------------
def test_no_grouped_speaker_gives_no_block():
    presence.reset_state()
    db = DB()
    assert lines(db, [bot(), NPC]) == []
    assert lines(db, [bot(grp={})]) == []
    assert lines(db, [bot(grp={'group_id': 0})]) == []
    assert db.queries == []


def test_disabled_gives_no_block():
    presence.reset_state()
    assert lines(DB(), [bot(grp=group())],
                 {'LLMChatter.GroupAwareness.Enable': '0'}) == []


def test_roster_colocation_and_rule():
    presence.reset_state()
    text = '\n'.join(lines(DB(), [bot(grp=group())]))
    assert 'Thalia (Thunder Bluff, Mulgore): in a party with' in text
    assert 'Rob (the player, here)' in text
    assert 'Vex (elsewhere in this zone)' in text
    assert 'Kael (elsewhere)' in text
    assert 'never offers to group with them' in text
    assert 'Mention only plans that appear above.' in text


def test_npc_and_ungrouped_speakers_know_nothing():
    presence.reset_state()
    text = '\n'.join(lines(DB(), [bot(grp=group()), NPC,
                                  bot('Jorin')]))
    assert 'Innkeeper Allison, Jorin know none of this.' in text


def test_other_group_has_no_link_to_anchor():
    presence.reset_state()
    other = group(9, members=[
        {'name': 'Kira', 'is_player': True, 'near': False,
         'same_zone': False}])
    text = '\n'.join(lines(DB(), [bot('Jorin', other)]))
    assert 'Jorin (Thunder Bluff, Mulgore): in a party with Kira' in text
    assert 'Rob' not in text


def test_no_group_association_inferred_from_absence():
    """The member list is only online members (or one raid subgroup),
    so a missing name never becomes a claim."""
    presence.reset_state()
    raid = group(raid=True, members=[
        {'name': 'Vex', 'is_player': False, 'near': True,
         'same_zone': True}])
    text = '\n'.join(lines(DB(), [bot(grp=raid)]))
    assert "not Rob's group" not in text
    assert 'in a raid; in their subgroup: Vex (here).' in text
    empty = '\n'.join(lines(DB(), [bot(grp=group(members=[]))]))
    assert 'Thalia (Thunder Bluff, Mulgore): in a party.' in empty
    assert 'never offers to group' not in empty


def test_instance_location_uses_speaker_self():
    presence.reset_state()
    grp = group()
    grp['self'] = {'zone_name': 'Desolace', 'area_name': 'Desolace',
                   'is_instance': True, 'map_name': 'Maraudon'}
    text = '\n'.join(lines(DB(), [bot(grp=grp)]))
    assert 'Thalia (inside Maraudon (Desolace))' in text


# ------------------------------------------------------------
# Private context and its boundary
# ------------------------------------------------------------
def test_delivered_lines_strict_join_second_boundary():
    presence.reset_state()
    db = DB(
        bot_rows=[
            {'name': 'Brosk', 'message': 'before join', 'ts': JOINED},
            {'name': 'Brosk', 'message': 'after join',
             'ts': JOINED + 1},
        ],
        player_rows=[
            {'name': 'Rob', 'message': 'old', 'ts': JOINED - 5},
            {'name': 'Rob', 'message': 'we go in after this',
             'ts': JOINED + 2},
        ])
    text = '\n'.join(lines(db, [bot(grp=group())]))
    assert 'before join' not in text and 'old' not in text
    assert 'Brosk: after join / Rob (player): we go in after this' \
        in text
    bot_query = next(q for q, _ in db.queries
                     if 'llm_chatter_messages' in q)
    for clause in ('delivered = 1', 'delivered_at IS NOT NULL',
                   'drop_reason IS NULL', 'UNIX_TIMESTAMP(delivered_at) >'):
        assert clause in bot_query, clause
    params = next(p for q, p in db.queries
                  if 'llm_chatter_messages' in q)
    assert params[0] == 'party' and params[1] == 5
    assert params[2] == JOINED


def test_most_recent_delivery_wins_over_insertion_order():
    """Concurrent generation and delayed delivery: the row inserted
    first (id 1) was heard last and must be kept with HistoryLines=1."""
    presence.reset_state()
    db = DB(
        bot_rows=[
            {'id': 1, 'name': 'Brosk', 'message': 'heard last',
             'ts': JOINED + 20},
            {'id': 2, 'name': 'Vex', 'message': 'heard first',
             'ts': JOINED + 10},
        ],
        player_rows=[
            {'id': 1, 'name': 'Rob', 'message': 'player late',
             'ts': JOINED + 15},
            {'id': 2, 'name': 'Rob', 'message': 'player early',
             'ts': JOINED + 5},
        ])
    config = {'LLMChatter.GroupAwareness.HistoryLines': 1}
    text = '\n'.join(lines(db, [bot(grp=group())], config))
    assert 'Brosk: heard last' in text
    assert 'heard first' not in text and 'player late' not in text
    config = {'LLMChatter.GroupAwareness.HistoryLines': 3}
    text = '\n'.join(lines(DB(bot_rows=db.bot_rows,
                               player_rows=db.player_rows),
                           [bot(grp=group())], config))
    assert ('Vex: heard first / Rob (player): player late / '
            'Brosk: heard last') in text


def test_history_lines_limit_and_zero():
    presence.reset_state()
    rows = [{'name': 'Brosk', 'message': f'line {i}',
             'ts': JOINED + i} for i in range(1, 7)]
    db = DB(bot_rows=rows)
    text = '\n'.join(lines(db, [bot(grp=group())],
                           {'LLMChatter.GroupAwareness.HistoryLines': 2}))
    assert 'line 5 / Brosk: line 6' in text and 'line 4' not in text
    db = DB(bot_rows=rows)
    text = '\n'.join(lines(db, [bot(grp=group())],
                           {'LLMChatter.GroupAwareness.HistoryLines': 0}))
    assert 'Lately in' not in text
    assert db.tables() == []


def test_raid_gets_raid_lines_only():
    presence.reset_state()
    feed(DB(event_ts={1: JOINED + 10}), 1, 'bot_group_dungeon_entry',
         {'map_name': 'Molten Core'})
    db = DB(bot_rows=[{'name': 'Brosk', 'message': 'pull at 3',
                       'ts': JOINED + 20}],
            player_rows=[{'name': 'Rob', 'message': 'secret',
                          'ts': JOINED + 20}])
    text = '\n'.join(lines(db, [bot(grp=group(raid=True))]))
    assert 'in a raid; in their subgroup:' in text
    assert 'Lately in raid chat (not said here): Brosk: pull at 3' in text
    assert 'secret' not in text and 'recently' not in text
    assert db.tables() == ['llm_chatter_messages']
    params = next(p for q, p in db.queries
                  if 'llm_chatter_messages' in q)
    assert params[0] == 'raid'


def test_bot_only_group_gets_roster_only():
    presence.reset_state()
    feed(DB(event_ts={1: JOINED + 10}), 1, 'bot_group_zone_transition',
         {'zone_name': 'The Barrens'})
    db = DB(bot_rows=[{'name': 'B', 'message': 'x', 'ts': JOINED + 9}])
    text = '\n'.join(lines(db, [bot(grp=group(real=False))]))
    assert 'in a party with' in text
    assert 'recently' not in text and 'Lately' not in text
    assert db.tables() == []


def test_unknown_member_since_gets_no_private_context():
    presence.reset_state()
    db = DB(bot_rows=[{'name': 'B', 'message': 'x', 'ts': NOW}])
    text = '\n'.join(lines(db, [bot(grp=group(since=0))]))
    assert 'Lately' not in text and db.tables() == []


def test_thread_topic_never_used():
    source = Path(presence.__file__).read_text(encoding='utf-8')
    assert 'import chatter_threads' not in source
    assert 'from chatter_threads' not in source
    presence.reset_state()
    text = '\n'.join(lines(DB(), [bot(grp=group())]))
    assert 'talking about' not in text


def test_threads_off_no_chat_still_has_facts():
    presence.reset_state()
    feed(DB(event_ts={1: JOINED + 30}), 1, 'bot_group_quest_accept',
         {'quest_name': 'The Corrupter', 'quest_id': 77})
    text = '\n'.join(lines(DB(), [bot(grp=group())],
                           {'LLMChatter.Threads.Enable': '0'}))
    assert 'Rob (the player, here)' in text
    assert 'Thunder Bluff' in text
    assert 'The party recently picked up the quest "The Corrupter".' \
        in text


# ------------------------------------------------------------
# Activity ring
# ------------------------------------------------------------
def test_ring_uses_event_row_time_and_join_boundary():
    presence.reset_state()
    db = DB(event_ts={1: JOINED, 2: JOINED + 1})
    feed(db, 1, 'bot_group_kill',
         {'creature_name': 'Hogger', 'is_boss': 1})
    feed(db, 2, 'bot_group_kill',
         {'creature_name': 'Van Cleef', 'is_boss': 1})
    feed(db, 3, 'bot_group_kill',
         {'creature_name': 'Rat', 'is_boss': 0})
    text = '\n'.join(lines(DB(), [bot(grp=group())]))
    assert 'defeated Van Cleef' in text
    assert 'Hogger' not in text and 'Rat' not in text


def test_ring_out_of_order_accept_stays_completed():
    presence.reset_state()
    db = DB(event_ts={1: JOINED + 50, 2: JOINED + 20})
    feed(db, 1, 'bot_group_quest_complete',
         {'quest_name': 'Q', 'quest_id': 9})
    feed(db, 2, 'bot_group_quest_accept',
         {'quest_name': 'Q', 'quest_id': 9})
    text = '\n'.join(lines(DB(), [bot(grp=group())]))
    assert 'turned in the quest "Q"' in text
    assert 'picked up the quest "Q"' not in text


def test_ring_batch_accept_meets_completion_by_name():
    presence.reset_state()
    db = DB(event_ts={1: JOINED + 10, 2: JOINED + 40})
    feed(db, 1, 'bot_group_quest_accept_batch',
         {'quest_names': ['The Corrupter', 'Other']})
    feed(db, 2, 'bot_group_quest_complete',
         {'quest_name': 'The Corrupter', 'quest_id': 77})
    text = '\n'.join(lines(DB(), [bot(grp=group())]))
    assert 'turned in the quest "The Corrupter"' in text
    assert 'picked up the quest "The Corrupter"' not in text
    assert 'picked up the quest "Other"' in text


def test_ring_reconcile_drops_ended_groups():
    presence.reset_state()
    db = DB(event_ts={1: JOINED + 10, 2: JOINED + 10})
    feed(db, 1, 'bot_group_zone_transition',
         {'zone_name': 'Ashenvale'}, group_id=5)
    feed(db, 2, 'bot_group_zone_transition',
         {'zone_name': 'Durotar'}, group_id=6)
    with patch.object(presence.time, 'time', return_value=NOW):
        presence.reconcile_active_groups([6])
    assert 5 not in presence._rings and 6 in presence._rings
    feed(DB(event_ts={3: NOW - 1}), 3, 'bot_group_zone_transition',
         {'zone_name': 'Late'}, group_id=5)
    assert 5 not in presence._rings


def test_ring_end_all_sessions_blocks_late_events():
    presence.reset_state()
    with patch.object(presence.time, 'time', return_value=NOW):
        presence.end_all_sessions()
    feed(DB(event_ts={1: NOW - 1}), 1, 'bot_group_zone_transition',
         {'zone_name': 'Late'}, group_id=8)
    assert 8 not in presence._rings
    feed(DB(event_ts={2: NOW + 1}), 2, 'bot_group_zone_transition',
         {'zone_name': 'New'}, group_id=8)
    assert 8 in presence._rings
    presence.reset_state()


def test_ring_tombstone_blocks_late_events():
    presence.reset_state()
    with patch.object(presence.time, 'time', return_value=NOW):
        presence.clear_group(5)
    feed(DB(event_ts={1: NOW - 10}), 1, 'bot_group_zone_transition',
         {'zone_name': 'The Barrens'})
    text = '\n'.join(lines(DB(), [bot(grp=group())]))
    assert 'Barrens' not in text


def test_ring_bounds_and_window():
    presence.reset_state()
    config = {'LLMChatter.GroupAwareness.ActivityMaxEntries': 2}
    db = DB(event_ts={i: JOINED + i for i in range(1, 5)})
    for i in range(1, 5):
        feed(db, i, 'bot_group_zone_transition',
             {'zone_name': f'Zone{i}'}, config=config)
    assert len(presence._rings[5]) == 2
    text = '\n'.join(lines(DB(), [bot(grp=group())], config))
    assert 'Zone3' in text and 'Zone4' in text and 'Zone1' not in text
    stale = {'LLMChatter.GroupAwareness.WindowSeconds': 60}
    text = '\n'.join(lines(DB(), [bot(grp=group())], stale))
    assert 'Zone4' not in text


def test_ring_concurrent_writes_stay_bounded():
    presence.reset_state()
    db = DB(event_ts={i: JOINED + i for i in range(1, 201)})

    def worker(start):
        for i in range(start, start + 50):
            feed(db, i, 'bot_group_zone_transition',
                 {'zone_name': f'Z{i}'})

    threads = [threading.Thread(target=worker, args=(s,))
               for s in (1, 51, 101, 151)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    ring = list(presence._rings[5])
    assert len(ring) == 5
    assert [e[0] for e in ring] == sorted(e[0] for e in ring)


# ------------------------------------------------------------
# Proximity wiring
# ------------------------------------------------------------
EXTRA = {
    'player_name': 'Rob', 'player_guid': 7, 'zone_id': 215,
    'area_id': 222, 'map_id': 1, 'zone_name': 'Mulgore',
    'subzone_name': 'Thunder Bluff', 'nearby_names': ['Vex'],
    'max_lines': 2,
}


def _prompt_text(prompt):
    return getattr(prompt, 'user_prompt', str(prompt))


def test_proximity_prompt_unchanged_without_grouped_speaker():
    import random
    presence.reset_state()
    db = DB()
    random.seed(94)
    base = _prompt_text(prox._conversation_prompt(
        db, dict(EXTRA), [dict(NPC), bot()],
        {'LLMChatter.GroupAwareness.Enable': '0'}))
    random.seed(94)
    again = _prompt_text(prox._conversation_prompt(
        db, dict(EXTRA), [dict(NPC), bot(grp={})], {}))
    assert 'What each speaker knows' not in again
    assert base == again
    random.seed(7)
    single_base = _prompt_text(prox._single_prompt(
        db, dict(EXTRA), bot(), 'weather',
        config={'LLMChatter.GroupAwareness.Enable': '0'}))
    random.seed(7)
    single = _prompt_text(prox._single_prompt(
        db, dict(EXTRA), bot(), 'weather', config={}))
    assert single_base == single


def test_proximity_conversation_has_block_and_tags_companions():
    presence.reset_state()
    grp = group(members=[{'name': 'Vex', 'is_player': False,
                          'near': True, 'same_zone': True}])
    text = _prompt_text(prox._conversation_prompt(
        DB(), dict(EXTRA), [dict(NPC), bot(grp=grp)], {}))
    assert 'What each speaker knows about their own group' in text
    assert 'Innkeeper Allison knows none of this.' in text
    assert 'Vex (travelling with Thalia)' in text


def test_disabled_restores_old_prompt_with_near_member():
    import random
    presence.reset_state()
    near = group(members=[{'name': 'Vex', 'is_player': False,
                           'near': True, 'same_zone': True}])
    off = {'LLMChatter.GroupAwareness.Enable': '0'}
    random.seed(3)
    base = _prompt_text(prox._conversation_prompt(
        DB(), dict(EXTRA), [dict(NPC), bot()], off))
    random.seed(3)
    disabled = _prompt_text(prox._conversation_prompt(
        DB(), dict(EXTRA), [dict(NPC), bot(grp=near)], off))
    assert base == disabled
    assert presence.tag_companions(['Vex'], [bot(grp=near)], off) \
        == ['Vex']


def test_tag_companions_only_near_members():
    speakers = [bot(grp=group())]
    assert presence.tag_companions(['Rob', 'Vex', 'Zed'], speakers) == [
        'Rob (travelling with Thalia)', 'Vex', 'Zed']
    assert presence.tag_companions(['Rob'], [bot()]) == ['Rob']


def main() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} group awareness checks passed")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
