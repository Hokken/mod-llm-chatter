#!/usr/bin/env python3
"""Focused regression checks for curated non-humanoid proximity speech."""

import importlib
import sys
import types
from pathlib import Path


def _ensure_module(name):
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


for dependency in ('anthropic', 'openai'):
    try:
        importlib.import_module(dependency)
    except ModuleNotFoundError:
        module = _ensure_module(dependency)
        attribute = (
            'Anthropic' if dependency == 'anthropic'
            else 'OpenAI'
        )
        setattr(module, attribute, type(attribute, (), {}))

try:
    importlib.import_module('mysql.connector')
except ModuleNotFoundError:
    mysql_module = _ensure_module('mysql')
    connector_module = _ensure_module('mysql.connector')
    setattr(mysql_module, 'connector', connector_module)

TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_DIR = TOOLS_DIR.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from chatter_proximity import (  # noqa: E402
    _conversation_prompt,
    _single_prompt,
)
from chatter_event_registry import EVENT_REGISTRY  # noqa: E402


class _DB:
    def cursor(self, *args, **kwargs):
        raise AssertionError('NPC prompt must not query bot identity')


NORMAL_CONFIG = {'LLMChatter.ChatterMode': 'normal'}
INSTANCE_EXTRA = {
    'player_guid': 42,
    'player_name': 'Calwen',
    'zone_id': 209,
    'zone_name': 'Shadowfang Keep',
    'subzone_name': 'The Courtyard',
    'map_id': 33,
    'instance_id': 12,
    'map_name': 'Shadowfang Keep',
    'is_dungeon': True,
    'is_raid': False,
    'nearby_names': [],
    'max_lines': 2,
}
CONFIGURED_DRAGONKIN = {
    'name': 'Wyrmrest Emissary',
    'is_npc': True,
    'npc_entry': 99002,
    'npc_spawn_id': 9001,
    'role': 'NPC',
    'sub_name': 'Ruby Envoy',
    'disposition': 'hostile',
    'rank': 'elite',
    'creature_type': 'dragonkin',
    'qualification': 'configured entry',
}
FUNCTIONAL_MECHANICAL = {
    'name': 'Clockwork Assistant',
    'is_npc': True,
    'npc_entry': 99001,
    'npc_spawn_id': 9002,
    'role': 'Quest Giver',
    'sub_name': 'Workshop Liaison',
    'disposition': 'friendly',
    'rank': 'normal',
    'creature_type': 'mechanical',
    'qualification': 'functional NPC',
}


def test_configured_non_humanoid_metadata_reaches_single_prompt():
    prompt = _single_prompt(
        _DB(), INSTANCE_EXTRA, CONFIGURED_DRAGONKIN,
        'warn nearby intruders', config=NORMAL_CONFIG,
    ).user_prompt
    assert 'creature type: dragonkin' in prompt
    assert 'qualified by: configured entry' in prompt
    assert 'this exact creature entry was deliberately approved' in prompt
    assert 'do not invent a persistent backstory' in prompt
    assert 'This NPC is hostile to the player' in prompt


def test_functional_non_humanoid_metadata_reaches_conversation():
    participants = [FUNCTIONAL_MECHANICAL, CONFIGURED_DRAGONKIN]
    prompt = _conversation_prompt(
        _DB(), {**INSTANCE_EXTRA, 'participants': participants},
        participants, config=NORMAL_CONFIG,
    ).user_prompt
    assert 'creature type: mechanical' in prompt
    assert 'qualified by: functional NPC' in prompt
    assert 'creature type: dragonkin' in prompt
    assert 'intentionally capable of speech' in prompt
    assert 'every creature of its type can talk' in prompt


def test_cpp_policy_order_is_conservative_and_global():
    source = (
        MODULE_DIR / 'src' / 'LLMChatterProximity.cpp'
    ).read_text(encoding='utf-8')
    policy = source.split(
        'ProximityNPCQualification GetProximityNPCQualification(', 1
    )[1].split(
        'std::string GetProximityNPCQualificationLabel(', 1
    )[0]
    ordered = [
        'IsProximitySpeakerDenied(entry)',
        'IsLLMChatterBoss(creature)',
        'creature->IsGuard()',
        'HasConversationalNPCFlags(creature)',
        'CREATURE_TYPE_HUMANOID',
        'IsProximitySpeakerAllowed(entry)',
    ]
    positions = [policy.index(item) for item in ordered]
    assert positions == sorted(positions)

    eligibility = source.split(
        'bool IsEligibleProximityNPC(', 1
    )[1].split('WorldObject* ResolveParticipantObject(', 1)[0]
    for safety_check in (
        'cr->IsAlive()',
        'player->IsWithinDistInMap(cr, radius)',
        'player->IsWithinLOSInMap(cr)',
        'cr->IsPet()',
        'cr->IsTotem()',
        'cr->IsGuardian()',
        'cr->IsInCombat()',
        'cr->GetSpawnId()',
        'cr->HasUnitFlag(UNIT_FLAG_NOT_SELECTABLE)',
        'IsLLMChatterInternalCreature(cr)',
        'cr->HasUnitState(UNIT_STATE_DIED)',
        'cr->HasDynamicFlag(UNIT_DYNFLAG_DEAD)',
        'player->CanSeeOrDetect(cr)',
    ):
        assert safety_check in eligibility
    assert 'cr->IsHostileTo(player)' not in eligibility
    assert 'HasUnsafeChatterFacingMotion(cr)' not in eligibility

    bot_eligibility = source.split(
        'bool IsEligibleProximityBot(', 1
    )[1].split('bool IsEligibleProximityNPC(', 1)[0]
    assert 'HasUnsafeChatterFacingMotion(bot)' not in bot_eligibility

    delivery = (
        MODULE_DIR / 'src' / 'LLMChatterDelivery.cpp'
    ).read_text(encoding='utf-8')
    assert 'IsSafeForChatterFacing(bot)' in delivery
    assert 'IsSafeForChatterFacing(speaker)' in delivery

    shared = (
        MODULE_DIR / 'src' / 'LLMChatterShared.cpp'
    ).read_text(encoding='utf-8')
    internal = shared.split(
        'bool IsLLMChatterInternalCreature(', 1
    )[1].split('std::string SanitizeUtf8(', 1)[0]
    for marker in (
        '[DND]', '(DND)', '[PH]', '(PH)', '[UNUSED]', '(UNUSED)',
    ):
        assert marker in internal
    assert 'creature->IsTrigger()' in internal
    assert 'StringContainsStringI(name, marker)' in internal


def test_nearby_name_context_deduplicates_names_and_typed_ids():
    source = (
        MODULE_DIR / 'src' / 'LLMChatterProximity.cpp'
    ).read_text(encoding='utf-8')
    nearby = source.split(
        'std::string BuildNearbyNamesJson(', 1
    )[1].split('std::string BuildProximityExtraJson(', 1)[0]
    assert 'std::set<std::pair<bool, uint32>> speakerIds' in nearby
    assert 'speakerIds.emplace(s.isNPC, s.id)' in nearby
    assert 'std::set<std::string> includedNames' in nearby
    assert 'ToLowerAscii(c.name)' in nearby

    selection = source.split(
        'std::vector<ProximityCandidate> SelectCompatibleSpeakers(', 1
    )[1].split('std::string ToLowerAscii(', 1)[0]
    assert 'StringEqualI(' in selection
    assert 'candidate.name, selected.name' in selection


def test_entry_lists_are_reload_safe_and_deny_wins():
    header = (
        MODULE_DIR / 'src' / 'LLMChatterConfig.h'
    ).read_text(encoding='utf-8')
    config = (
        MODULE_DIR / 'src' / 'LLMChatterConfig.cpp'
    ).read_text(encoding='utf-8')
    distributed = (
        MODULE_DIR / 'conf' / 'mod_llm_chatter.conf.dist'
    ).read_text(encoding='utf-8')
    for name in ('SpeakerAllowEntries', 'SpeakerDenyEntries'):
        assert name in config
        assert name in distributed
    assert '_proxSpeakerAllowEntries' in header
    assert '_proxSpeakerDenyEntries' in header
    assert 'std::atomic<std::shared_ptr<' in header
    assert '_proxSpeakerAllowEntries.store(' in config
    assert '_proxSpeakerDenyEntries.store(' in config
    assert 'configured.load()' in config
    assert 'LOG_WARN(' in config

    source = (
        MODULE_DIR / 'src' / 'LLMChatterProximity.cpp'
    ).read_text(encoding='utf-8')
    policy = source.split(
        'ProximityNPCQualification GetProximityNPCQualification(', 1
    )[1].split(
        'std::string GetProximityNPCQualificationLabel(', 1
    )[0]
    assert policy.index('IsProximitySpeakerDenied(entry)') < (
        policy.index('IsProximitySpeakerAllowed(entry)')
    )


def test_reply_payload_preserves_non_humanoid_grounding():
    cpp = (
        MODULE_DIR / 'src' / 'LLMChatterProximity.cpp'
    ).read_text(encoding='utf-8')
    python = (
        MODULE_DIR / 'tools' / 'chatter_proximity.py'
    ).read_text(encoding='utf-8')
    assert 'responder_creature_type' in cpp
    assert 'responder_qualification' in cpp
    assert "'responder_creature_type'" in python
    assert "'responder_qualification'" in python
    fields = EVENT_REGISTRY['proximity_reply'].payload_fields
    assert 'responder_creature_type' in fields
    assert 'responder_qualification' in fields


def main():
    tests = [
        value for name, value in globals().items()
        if name.startswith('test_') and callable(value)
    ]
    for test in tests:
        test()
    print(f'{len(tests)} non-humanoid proximity tests passed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
