#!/usr/bin/env python3
"""Source contract checks for addon profile edits.

The C++ side has no test harness, so these pin the parts of the
transaction contract that a refactor could silently undo.
"""

from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[2] / 'src'
COMMAND = (SRC_DIR / 'LLMChatterCommand.cpp').read_text(encoding='utf-8')


def _function_body(source, signature):
    body = source.split(signature, 1)[1]
    return body.split('\n}\n', 1)[0]


def test_regeneration_jobs_are_part_of_the_transaction():
    # A session that goes offline drops its transaction callback
    # unrun, so the jobs must not be queued from that callback.
    commit = _function_body(COMMAND, 'void CommitProfileEdit(')
    append_at = commit.index('AppendRegenerationEvents(trans, edit);')
    submit_at = commit.index('AsyncCommitTransaction(trans)')
    assert append_at < submit_at

    regen = _function_body(COMMAND, 'void AppendRegenerationEvents(')
    assert regen.count('AppendChatterEvent(') == 2
    assert '"bot_tone_regen"' in regen
    assert '"bot_backstory_regen"' in regen
    assert 'if (!edit.hasBackstory)' in regen


def test_session_callback_only_replies_to_the_addon():
    report = _function_body(COMMAND, 'void ReportProfileEdit(')
    assert 'QueueChatterEvent(' not in report
    assert 'AppendChatterEvent(' not in report
    assert 'CharacterDatabase' not in report


def test_decoder_accepts_the_tilde_escape():
    # The client rewrites %f in outgoing chat, so the addon sends
    # bytes 0xF0-0xFF as ~FX. The addon's Lua suite checks the
    # round trip against a mirror of this decoder.
    decode = _function_body(COMMAND, 'std::string PercentDecode(')
    assert "input[i] == '~'" in decode
    assert "input[i + 1] == 'F'" in decode
    assert "input[i + 1] == 'f'" in decode


def main():
    tests = [
        value for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f'{len(tests)} profile-edit transaction tests passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
