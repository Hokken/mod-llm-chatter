"""TTS engines, voice map and audio maths for the host voice agent.

Kept free of audio/DB imports so it can be unit-tested anywhere.
httpx is imported lazily by the ElevenLabs engine.
"""

import json
import logging
import math
from collections import OrderedDict
from pathlib import Path

from chatter_links import clean_link_markup
from chatter_text import strip_emojis

log = logging.getLogger(__name__)

ELEVENLABS_API = 'https://api.elevenlabs.io'
PCM_FORMATS = {'pcm_16000': 16000, 'pcm_22050': 22050, 'pcm_24000': 24000}
GENDER_MALE = 0
GENDER_FEMALE = 1


class SynthesisError(Exception):
    """A single clip failed; the row is dropped."""


class QuotaExhausted(SynthesisError):
    """The provider refuses further synthesis for this session."""


# -----------------------------------------------------------
# Text, gain and pan
# -----------------------------------------------------------

def clean_voice_text(text: str) -> str:
    """Speakable text: link markup to names, no brackets or emojis."""
    if not text:
        return ''
    text = clean_link_markup(text).replace('[', '').replace(']', '')
    return ' '.join(strip_emojis(text).split())


def compute_gain(distance: float, radius: float, falloff: str,
                 ref_distance: float, rolloff: float, min_gain: float,
                 master: float) -> float:
    """Distance attenuation in [min_gain, 1], scaled by master (0-1)."""
    distance = max(0.0, distance)
    if falloff == 'linear':
        gain = 1.0 - distance / radius if radius > 0 else 1.0
    else:
        excess = max(0.0, distance - ref_distance)
        denom = ref_distance + rolloff * excess
        gain = ref_distance / denom if denom > 0 else 1.0
    return max(min_gain, min(1.0, gain)) * master


def compute_pan(rel_angle: float, width: float) -> tuple:
    """Constant-power (left, right) gains for a relative bearing.

    rel_angle is counter-clockwise from the listener's facing, so a
    positive angle is to the left.
    """
    pan = max(-1.0, min(1.0, -math.sin(rel_angle) * width))
    theta = (pan + 1.0) * math.pi / 4.0
    return math.cos(theta), math.sin(theta)


# -----------------------------------------------------------
# Voice map
# -----------------------------------------------------------

class VoiceMap:
    """race/gender -> voice id, via archetypes, with fallbacks."""

    def __init__(self, data: dict):
        self.race_archetype = {}
        self.archetypes = {}
        self.defaults = {}
        self.unknown_gender = GENDER_MALE
        self._load(data if isinstance(data, dict) else {})

    @staticmethod
    def _voice_id(entry) -> str:
        if isinstance(entry, dict):
            value = entry.get('voice_id', '')
            return value.strip() if isinstance(value, str) else ''
        return ''

    def _genders(self, block, label: str) -> dict:
        voices = {}
        if not isinstance(block, dict):
            log.warning('Voice map: %s is not an object; ignored', label)
            return voices
        for key, gender in (('male', GENDER_MALE),
                            ('female', GENDER_FEMALE)):
            voices[gender] = self._voice_id(block.get(key))
        return voices

    def _load(self, data: dict) -> None:
        fallback = data.get('unknown_gender', 'male')
        self.unknown_gender = (GENDER_FEMALE if fallback == 'female'
                               else GENDER_MALE)
        self.defaults = self._genders(data.get('defaults', {}), 'defaults')
        archetypes = data.get('archetypes', {})
        if not isinstance(archetypes, dict):
            log.warning('Voice map: archetypes is not an object; ignored')
            archetypes = {}
        for name, block in archetypes.items():
            if not isinstance(block, dict):
                log.warning('Voice map: archetype %s is not an object; '
                            'ignored', name)
                continue
            self.archetypes[name] = self._genders(block, name)
            races = block.get('races', [])
            if not isinstance(races, list):
                log.warning('Voice map: races of %s is not a list; '
                            'ignored', name)
                races = []
            for race in races:
                if isinstance(race, int) and not isinstance(race, bool):
                    self.race_archetype[race] = name
                else:
                    log.warning('Voice map: bad race id %r in %s; '
                                'ignored', race, name)

    def resolve(self, race: int, gender: int,
                unsupported=frozenset()) -> str:
        """Voice id for a speaker, or '' when nothing usable is set.

        Empty or unsupported ids fall through to the gender default,
        then the male default.
        """
        if gender not in (GENDER_MALE, GENDER_FEMALE):
            gender = self.unknown_gender
        archetype = self.archetypes.get(self.race_archetype.get(race), {})
        for voice in (archetype.get(gender), self.defaults.get(gender),
                      self.defaults.get(GENDER_MALE)):
            if voice and voice not in unsupported:
                return voice
        return ''

    def entries(self):
        """(label, gender, voice_id) for every configured slot."""
        for gender, voice in self.defaults.items():
            yield 'defaults', gender, voice
        for name, voices in self.archetypes.items():
            for gender, voice in voices.items():
                yield name, gender, voice


def load_voice_map(path: str) -> VoiceMap:
    try:
        data = json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        log.error('Voice map %s unreadable: %s', path, exc)
        data = {}
    return VoiceMap(data)


# -----------------------------------------------------------
# Clip cache
# -----------------------------------------------------------

class LruClipCache:
    """PCM clips keyed by (voice, model, text), bounded by bytes."""

    def __init__(self, max_bytes: int):
        self.max_bytes = max(0, max_bytes)
        self.size = 0
        self._items = OrderedDict()

    def get(self, key):
        clip = self._items.get(key)
        if clip is not None:
            self._items.move_to_end(key)
        return clip

    def put(self, key, pcm: bytes) -> None:
        if len(pcm) > self.max_bytes:
            return
        old = self._items.pop(key, None)
        if old is not None:
            self.size -= len(old)
        self._items[key] = pcm
        self.size += len(pcm)
        while self.size > self.max_bytes:
            _, evicted = self._items.popitem(last=False)
            self.size -= len(evicted)


# -----------------------------------------------------------
# Engines
# -----------------------------------------------------------

class TTSEngine:
    """Provider adapter: text + voice id -> 16-bit mono PCM."""

    sample_rate = 22050
    model = ''

    def synthesize(self, text: str, voice_id: str,
                   timeout: float) -> bytes:
        raise NotImplementedError

    def list_voices(self) -> list:
        return []

    def quota(self):
        return None


class ElevenLabsEngine(TTSEngine):
    def __init__(self, api_key: str, model: str, output_format: str,
                 client=None):
        if output_format not in PCM_FORMATS:
            raise ValueError(f'unsupported output format {output_format}')
        self.api_key = api_key
        self.model = model
        self.output_format = output_format
        self.sample_rate = PCM_FORMATS[output_format]
        if client is None:
            import httpx
            client = httpx.Client(base_url=ELEVENLABS_API)
        self.client = client

    def _headers(self) -> dict:
        return {'xi-api-key': self.api_key}

    @staticmethod
    def _is_quota_error(response) -> bool:
        if response.status_code not in (401, 402, 429):
            return False
        try:
            detail = response.json().get('detail', {})
        except ValueError:
            return False
        status = detail.get('status', '') if isinstance(detail, dict) else ''
        return status in ('quota_exceeded', 'payment_required')

    @staticmethod
    def _error_message(response) -> str:
        """Provider's own message (e.g. a missing key permission)."""
        try:
            detail = response.json().get('detail', {})
        except (ValueError, AttributeError):
            detail = None
        if isinstance(detail, dict) and detail.get('message'):
            return f"HTTP {response.status_code}: {detail['message']}"
        return f'HTTP {response.status_code}: {response.text[:200]}'

    def synthesize(self, text: str, voice_id: str,
                   timeout: float) -> bytes:
        try:
            response = self.client.post(
                f'/v1/text-to-speech/{voice_id}',
                params={'output_format': self.output_format},
                headers=self._headers(),
                json={'text': text, 'model_id': self.model},
                timeout=max(0.5, timeout))
        except Exception as exc:
            raise SynthesisError(f'request failed: {exc}') from exc
        if self._is_quota_error(response):
            raise QuotaExhausted('ElevenLabs quota exhausted')
        if response.status_code != 200:
            raise SynthesisError(self._error_message(response))
        return response.content

    def list_voices(self) -> list:
        """Account voices via the free /v2/voices endpoint."""
        voices = []
        token = None
        while True:
            params = {'page_size': 100}
            if token:
                params['next_page_token'] = token
            try:
                response = self.client.get('/v2/voices', params=params,
                                           headers=self._headers(),
                                           timeout=15)
            except Exception as exc:
                raise SynthesisError(
                    f'voice list request failed: {exc}') from exc
            if response.status_code != 200:
                raise SynthesisError(self._error_message(response))
            body = response.json()
            voices.extend(body.get('voices', []))
            token = body.get('next_page_token')
            if not body.get('has_more') or not token:
                return voices

    def quota(self):
        """(used, limit) characters for the billing period, or None."""
        try:
            response = self.client.get('/v1/user/subscription',
                                       headers=self._headers(),
                                       timeout=10)
            if response.status_code != 200:
                raise SynthesisError(self._error_message(response))
            body = response.json()
            return (body.get('character_count'),
                    body.get('character_limit'))
        except Exception as exc:
            log.warning('Quota lookup failed: %s', exc)
            return None
