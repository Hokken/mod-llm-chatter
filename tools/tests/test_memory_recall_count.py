"""Prompts retrieve the configured number of memories."""

import unittest

import test_persona_coherence  # dependency stubs and tools path
from chatter_memory import get_bot_memories, memory_recall_count


class _Cursor:
    def __init__(self, rows=()):
        self.params = None
        self.rows = list(rows)

    def execute(self, sql, params):
        if self.params is None:
            self.params = params

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class _DB:
    def __init__(self, rows=()):
        self.rows = rows
        self.last = _Cursor()

    def cursor(self, *args, **kwargs):
        self.last = _Cursor(self.rows)
        return self.last

    def commit(self):
        pass


class MemoryRecallCountTests(unittest.TestCase):
    def test_defaults_keep_three_and_two(self):
        self.assertEqual(memory_recall_count({}), 3)
        self.assertEqual(memory_recall_count({}, idle=True), 2)

    def test_configured_counts(self):
        config = {
            'LLMChatter.Memory.RecallCount': '5',
            'LLMChatter.Memory.IdleRecallCount': '1',
        }
        self.assertEqual(memory_recall_count(config), 5)
        self.assertEqual(memory_recall_count(config, idle=True), 1)

    def test_clamped_and_invalid_values(self):
        self.assertEqual(
            memory_recall_count({'LLMChatter.Memory.RecallCount': '0'}), 1
        )
        self.assertEqual(
            memory_recall_count({'LLMChatter.Memory.RecallCount': '50'}),
            10,
        )
        self.assertEqual(
            memory_recall_count(
                {'LLMChatter.Memory.IdleRecallCount': 'many'}, idle=True
            ),
            2,
        )

    def test_count_limits_the_result(self):
        # Recall scores every active memory, then keeps `count`.
        rows = [
            {'id': i, 'memory': f'memory {i}',
             'memory_type': 'ambient', 'zone_id': None,
             'map_id': None, 'companions': None,
             'created_at': None, 'last_used_at': None}
            for i in range(1, 7)
        ]
        db = _DB(rows)
        result = get_bot_memories(
            db, 11, 22,
            count=memory_recall_count(
                {'LLMChatter.Memory.RecallCount': '4'}
            ),
        )
        self.assertEqual(len(result), 4)
        self.assertEqual(db.last.params[:2], (11, 22))


if __name__ == '__main__':
    unittest.main()
