"""Native response contracts, schema validation and legacy normalization.

This module owns wire shapes, not provider SDKs, delivery or domain policy.
Context stays in prompts/normalization and never changes an API schema.
"""

from dataclasses import dataclass
from functools import lru_cache
import json

from chatter_constants import EMOTE_LIST


# Legacy prompts include 'none'; native contracts use JSON null for absence.
EMOTES = tuple(emote for emote in EMOTE_LIST if emote != 'none')
VISION_TAGS = {
    'landmark_type': (
        'castle', 'ruins', 'bridge', 'tower', 'cave', 'waterfall',
        'lake', 'river', 'camp', 'village', 'city', 'ship', 'gate',
        'statue', 'shrine', 'none',
    ),
    'weather': ('clear', 'cloudy', 'foggy', 'rainy', 'snowy', 'stormy',
                'none'),
    'time_of_day': ('dawn', 'day', 'dusk', 'night', 'unknown'),
    'biome': ('forest', 'tundra', 'desert', 'swamp', 'mountain',
              'coastal', 'plains', 'volcanic', 'underground', 'urban',
              'none'),
}


class StructuredOutputError(ValueError):
    """A complete provider response failed its declared contract."""


class StructuredDependencyError(ImportError):
    """The local schema validator or one of its dependencies is unavailable."""


def structured_output_enabled(config):
    """Read the one global switch using the bridge's 0/1 convention."""
    return str(config.get('LLMChatter.StructuredOutput.Enable', '0')).strip() == '1'


@dataclass(frozen=True)
class ResponseContract:
    kind: str
    message_only: bool = False
    emote: bool = False
    action: str = 'none'
    addressee: bool = False
    thread: bool = False
    emote_only: bool = False
    speaker_names: tuple = ()
    addressee_names: tuple = ()
    thread_speaker_names: tuple = ()
    message_count: int = 0

    def __post_init__(self):
        if self.kind not in (
            'statement', 'conversation', 'analysis', 'memory', 'vision',
        ):
            raise ValueError('Unknown response contract kind')
        if self.action not in ('none', 'optional', 'required'):
            raise ValueError('Unknown action policy')
        for key in ('speaker_names', 'addressee_names',
                    'thread_speaker_names'):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        if self.kind not in ('statement', 'conversation') and any((
            self.message_only, self.emote, self.action != 'none',
            self.addressee, self.thread, self.emote_only,
        )):
            raise ValueError('Dialogue options require a dialogue contract')
        if self.message_only and any((
            self.emote, self.action != 'none', self.addressee,
            self.emote_only,
        )):
            raise ValueError('Message-only contract has incompatible fields')
        if self.addressee and self.kind != 'conversation':
            raise ValueError('Addressees require a conversation contract')
        if self.emote_only and not self.emote:
            raise ValueError('Emote-only output requires emotes')
        if self.thread and (
            not self.thread_speaker_names
            or any(not isinstance(name, str) or not name.strip()
                   for name in self.thread_speaker_names)
        ):
            raise ValueError('Thread reports require an explicit speaker roster')

    @property
    def schema_key(self):
        """Only options that affect the schema enter the bounded cache."""
        return (self.kind, self.message_only, self.emote, self.action,
                self.addressee, self.thread)


def statement_contract(*, message_only=False, emote=False,
                       action=False, emote_only=False, thread=False,
                       thread_speaker_names=()):
    # Unlike conversations, eligible statements do not mandate an action.
    return ResponseContract(
        'statement', message_only=message_only,
        emote=emote and not message_only,
        action='optional' if action and not message_only else 'none',
        emote_only=emote_only and emote and not message_only,
        thread=thread, thread_speaker_names=thread_speaker_names,
    )


def conversation_contract(speaker_names, message_count, *,
                          message_only=False, emote=False, action=False,
                          addressee_names=(), emote_only=False,
                          thread=False, thread_speaker_names=()):
    return ResponseContract(
        'conversation', message_only=message_only,
        emote=emote and not message_only,
        action='required' if action and not message_only else 'none',
        addressee=bool(addressee_names) and not message_only,
        emote_only=emote_only and emote and not message_only,
        thread=thread, speaker_names=speaker_names,
        addressee_names=addressee_names, message_count=message_count,
        thread_speaker_names=thread_speaker_names,
    )


def _object(properties):
    return {
        'type': 'object', 'properties': properties,
        'required': list(properties), 'additionalProperties': False,
    }


def _nullable(schema):
    return {'anyOf': [schema, {'type': 'null'}]}


def _string():
    return {'type': 'string'}


def _enum(values):
    return {'type': 'string', 'enum': list(values)}


def _report_schema():
    return _object({
        'topic': _string(),
        'energy': _enum(('high', 'medium', 'low', 'spent')),
        'subject_changed': {'type': 'boolean'},
        'open_point': _string(),
        'feelings': {'type': 'array', 'items': _object({
            'speaker': _string(), 'feeling': _string(),
        })},
    })


def _build_schema(key):
    kind, message_only, emote, action, addressee, thread = key
    if kind == 'analysis':
        return _object({
            'bot': _nullable(_string()),
            'multi_addressed': {'type': 'boolean'},
            'brief_casual': {'type': 'boolean'},
            'requires_reply': {'type': 'boolean'},
        })
    if kind == 'memory':
        return _object({'memory': _string(),
                        'emote': _nullable(_enum(EMOTES))})
    if kind == 'vision':
        return _object({
            **{name: _nullable(_enum(values))
               for name, values in VISION_TAGS.items()},
            **{name: _nullable(_string()) for name in (
                'atmosphere', 'environment', 'creatures', 'skip_reason',
            )},
        })
    item = {}
    if kind == 'conversation':
        item['speaker'] = _string()
    item['message'] = _string()
    if not message_only:
        item['emote'] = (_nullable(_enum(EMOTES)) if emote
                         else {'type': 'null'})
        item['action'] = (
            _string() if action == 'required' else
            _nullable(_string()) if action == 'optional' else
            {'type': 'null'}
        )
    if addressee:
        item['addressee'] = _string()
    properties = ({'messages': {'type': 'array', 'items': _object(item)}}
                  if kind == 'conversation' else item)
    if thread:
        properties['thread'] = _nullable(_report_schema())
    return _object(properties)


@lru_cache(maxsize=128)
def _validator(key):
    # Off-mode prompt metadata does not need this optional runtime import.
    from jsonschema import Draft202012Validator
    return Draft202012Validator(_build_schema(key))


def schema_for(contract):
    """Return a stable identifier and an independently mutable wire schema."""
    kind, message, emote, action, addressee, thread = contract.schema_key
    name = (f'chatter_{kind}_v1_m{int(message)}e{int(emote)}'
            f'a{action}_d{int(addressee)}t{int(thread)}')
    return name, _build_schema(contract.schema_key)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise StructuredOutputError('Duplicate JSON object key')
        result[key] = value
    return result


def _invalid_constant(value):
    raise StructuredOutputError('Non-JSON numeric constant')


def _normalize_report(report, names):
    if report is None:
        return None
    known = {name.casefold(): name for name in names}
    feelings = {}
    for entry in report['feelings']:
        name = known.get(entry['speaker'].strip().casefold())
        if name is None:
            continue
        if name in feelings:
            return None
        feelings[name] = entry['feeling']
    return {**report, 'feelings': feelings}


def validate_and_normalize(raw_text, contract):
    """Validate the entire response before exposing it to legacy parsers."""
    try:
        from jsonschema import ValidationError
        validator = _validator(contract.schema_key)
    except ImportError as exc:
        raise StructuredDependencyError('Schema validator unavailable') from exc
    try:
        if not isinstance(raw_text, str):
            raise StructuredOutputError('Response is not text')
        data = json.loads(raw_text, object_pairs_hook=_unique_object,
                          parse_constant=_invalid_constant)
        validator.validate(data)
    except (ValueError, TypeError, RecursionError, ValidationError) as exc:
        # Never include untrusted response contents in normal diagnostics.
        raise StructuredOutputError('Invalid structured response') from exc

    if contract.kind not in ('statement', 'conversation'):
        return json.dumps(data, ensure_ascii=False)
    messages = (data['messages'] if contract.kind == 'conversation'
                else [data])
    for message in messages:
        if not message['message'].strip() and not (
            contract.emote_only and message.get('emote')
        ):
            raise StructuredOutputError('Empty spoken response')
    report = None
    if contract.thread:
        report = _normalize_report(
            data.pop('thread'), contract.thread_speaker_names,
        )
    if contract.kind == 'conversation':
        data = messages
        if report is not None:
            data.append({'thread': report})
    elif report is not None:
        data['thread'] = report
    return json.dumps(data, ensure_ascii=False)


def render_structured_format(contract, semantic_rules=''):
    """Render valid dialogue examples without rewriting semantic guidance."""
    if contract.kind not in ('statement', 'conversation'):
        raise ValueError('Bespoke contracts retain their existing prompts')

    def example(speaker=None):
        item = {'message': '...'}
        if speaker is not None:
            item = {'speaker': speaker, **item}
        if not contract.message_only:
            item.update(emote=None, action=(
                'glances around' if contract.action != 'none' else None
            ))
        if contract.addressee:
            item['addressee'] = next((
                name for name in contract.addressee_names
                if name.casefold() != speaker.casefold()
            ), '')
        return item

    data = ({'messages': [example(name) for name in contract.speaker_names]}
            if contract.kind == 'conversation' else example())
    if contract.thread:
        data['thread'] = {
            'topic': 'current subject', 'energy': 'medium',
            'subject_changed': False, 'open_point': '', 'feelings': [],
        }
    count_rule = (
        f'Return EXACTLY {contract.message_count} messages in "messages".\n'
        if contract.kind == 'conversation' else ''
    )
    thread_rule = (
        'The thread is private bookkeeping, never spoken chat. Use null '
        'when absent. Its feelings is an array of {"speaker": "name", '
        '"feeling": "what is still on their mind, max 12 words"}; '
        'use [] when empty. Only use these report speakers: '
        + ', '.join(contract.thread_speaker_names) + '.\n'
        if contract.thread else ''
    )
    emote_rule = ''
    if not contract.message_only:
        emote_rule = (
            'Emotes: pick one that fits the mood from: '
            + ', '.join(EMOTES) + '; or use null.\n'
            if contract.emote else 'Emotes: use null for every emote.\n'
        )
    return (
        '\n\nRESPONSE FORMAT: Return ONLY one valid JSON object matching '
        'the supplied schema. No other text, markdown or code fences.\n'
        + json.dumps(data, ensure_ascii=False, indent=2) + '\n'
        + count_rule + thread_rule + emote_rule + semantic_rules
    )
