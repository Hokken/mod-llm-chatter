#!/usr/bin/env python3
"""Names that reach a prompt follow LLMChatter.Language, not the server.

sWorld->GetDefaultDbcLocale() is the worldserver's client locale and has
nothing to do with the module's own LLMChatter.Language. The two agree on
most servers, which is exactly why the mismatch survived so long: an
English worldserver configured for Russian chatter fed English spell and
achievement names into the prompt, and unlike creature, item and quest
names those carry no id for the bridge to re-resolve from.

One lookup keeps the worldserver locale on purpose, and that is asserted
here too so nobody 'fixes' it later: CanSpeakInGeneralChannel() compares a
zone name against live channel names, which the core creates in the
worldserver's locale.

Run directly from the module root:
  python tools/tests/test_module_locale_authority.py
"""

import re
import sys
from pathlib import Path

MODULE_ROOT = Path(__file__).resolve().parent.parent.parent
SRC = MODULE_ROOT / 'src'

# Every file whose name lookups feed prompt text.
PROMPT_SOURCES = (
    'LLMChatterShared.cpp',
    'LLMChatterPlayer.cpp',
    'LLMChatterProximity.cpp',
    'LLMChatterNearby.cpp',
    'LLMChatterGroupCombat.cpp',
    'LLMChatterDelivery.cpp',
)

SERVER_LOCALE = 'sWorld->GetDefaultDbcLocale()'
MODULE_LOCALE = 'sLLMChatterConfig->GetModuleLocale()'


def _read(name):
    return (SRC / name).read_text(encoding='utf-8')


def test_spell_and_achievement_names_use_the_module_locale():
    """The two Hokken's review named: no id exists to re-resolve them."""
    shared = _read('LLMChatterShared.cpp')
    for fn in ('GetLocalizedSpellName', 'GetLocalizedAchievementName'):
        body = re.search(
            r'std::string %s\([^)]*\)\s*\{(.*?)\n\}' % fn,
            shared, re.S)
        assert body, '%s not found' % fn
        assert MODULE_LOCALE in body.group(1), (
            '%s does not resolve through the module locale' % fn)
        assert SERVER_LOCALE not in body.group(1), (
            '%s still reads the worldserver locale' % fn)


def test_no_prompt_facing_lookup_reads_the_server_locale():
    """The whole class, not just the two that were reported."""
    offenders = []
    for name in PROMPT_SOURCES:
        text = _read(name)
        for i, line in enumerate(text.splitlines(), 1):
            if SERVER_LOCALE not in line:
                continue
            offenders.append('%s:%d' % (name, i))

    # The channel-name comparison is the one legitimate exception.
    allowed = [o for o in offenders
               if o.startswith('LLMChatterShared.cpp')]
    assert len(allowed) <= 1, (
        'more worldserver-locale lookups than the documented '
        'exception: %r' % offenders)
    assert len(offenders) == len(allowed), (
        'prompt-facing lookups still on the worldserver locale: %r'
        % [o for o in offenders if o not in allowed])


def test_channel_matching_keeps_the_worldserver_locale():
    """Deliberate exception: channels are named in the server's locale."""
    shared = _read('LLMChatterShared.cpp')
    body = re.search(
        r'bool CanSpeakInGeneralChannel\([^)]*\)\s*\{(.*?)\n\}',
        shared, re.S)
    assert body, 'CanSpeakInGeneralChannel not found'
    assert SERVER_LOCALE in body.group(1), (
        'channel matching must stay on the worldserver locale or it '
        'will not match any live channel name')


def test_every_supported_language_maps_to_a_locale():
    """The mapper must cover the codes the bridge itself accepts."""
    config = _read('LLMChatterConfig.cpp')
    mapper = re.search(
        r'LocaleConstant ResolveModuleLocale\([^)]*\)\s*\{(.*?)\n\}',
        config, re.S)
    assert mapper, 'ResolveModuleLocale not found'
    body = mapper.group(1)

    for code, locale in (
        ('RU', 'LOCALE_ruRU'),
        ('DE', 'LOCALE_deDE'),
        ('FR', 'LOCALE_frFR'),
        ('ES', 'LOCALE_esES'),
        ('KO', 'LOCALE_koKR'),
        ('US', 'LOCALE_enUS'),
        ('GB', 'LOCALE_enUS'),
    ):
        assert '"%s"' % code in body, 'language %s is unmapped' % code
        assert locale in body, '%s missing' % locale

    # Anything else keeps the previous behaviour rather than guessing.
    assert SERVER_LOCALE in body, (
        'unmapped languages must fall back to the worldserver locale')


def main() -> int:
    test_spell_and_achievement_names_use_the_module_locale()
    test_no_prompt_facing_lookup_reads_the_server_locale()
    test_channel_matching_keeps_the_worldserver_locale()
    test_every_supported_language_maps_to_a_locale()
    print('OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
