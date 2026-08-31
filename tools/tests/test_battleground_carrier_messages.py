#!/usr/bin/env python3
"""Focused battleground flag carrier message checks.

Run directly from the module root:
  python tools/tests/test_battleground_carrier_messages.py
"""

import sys
import types
from pathlib import Path
from unittest.mock import DEFAULT, patch


def _install_non_strict_stubs() -> None:
    for module_name, class_name in (
        ('anthropic', 'Anthropic'),
        ('openai', 'OpenAI'),
    ):
        try:
            __import__(module_name)
        except ModuleNotFoundError:
            module = types.ModuleType(module_name)
            setattr(module, class_name, type(class_name, (), {}))
            sys.modules[module_name] = module

    try:
        __import__('mysql.connector')
    except ModuleNotFoundError:
        mysql_module = types.ModuleType('mysql')
        connector_module = types.ModuleType('mysql.connector')
        mysql_module.connector = connector_module
        sys.modules['mysql'] = mysql_module
        sys.modules['mysql.connector'] = connector_module


TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
_install_non_strict_stubs()

import chatter_battlegrounds  # noqa: E402


def test_carrier_messages_use_event_type_as_delivery_reason():
    cases = (
        ('bg_flag_picked_up', 'carrier'),
        ('bg_flag_dropped', 'dropper'),
    )

    with patch.multiple(
        chatter_battlegrounds,
        get_lightweight_bot_data=DEFAULT,
        _maybe_talent_context=DEFAULT,
        build_bg_flag_carrier_prompt=DEFAULT,
        run_single_reaction=DEFAULT,
    ) as mocks:
        mocks['get_lightweight_bot_data'].return_value = {
            'class': 'Mage',
            'race': 'Human',
        }
        mocks['_maybe_talent_context'].return_value = None
        mocks['build_bg_flag_carrier_prompt'].return_value = 'prompt'
        run_single_reaction = mocks['run_single_reaction']

        for event_type, actor in cases:
            run_single_reaction.reset_mock()
            extra_data = {
                f'{actor}_name': 'Aliss',
                f'{actor}_guid': 101,
                f'{actor}_is_real_player': False,
                'team': 'Alliance',
            }
            chatter_battlegrounds._try_carrier_self_message(
                None, None, {}, 123,
                event_type, extra_data,
            )

            assert run_single_reaction.call_count == 1
            assert (
                run_single_reaction.call_args.kwargs[
                    'delivery_reason'
                ]
                == event_type
            )


if __name__ == '__main__':
    test_carrier_messages_use_event_type_as_delivery_reason()
    print('Battleground carrier message checks passed.')
