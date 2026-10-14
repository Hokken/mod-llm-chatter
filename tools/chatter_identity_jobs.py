"""Bounded profile preparation for bots joining reachable player guilds."""

from chatter_identity import config_int, ensure_bot_profile
from chatter_mode import is_roleplay
from chatter_shared import get_chatter_mode

_last_guid = 0


def guild_profiles_enabled(config):
    return (
        config_int(config, 'LLMChatter.Enable', 1)
        and config_int(config, 'LLMChatter.GuildChatter.Enable', 1)
        and is_roleplay(get_chatter_mode(config))
    )


# Session rows originate from the C++ real-player login path. Revalidate
# membership/online state rather than trusting a leftover session after a crash.
_ELIGIBLE = """
    FROM guild_member gm
    JOIN characters c ON c.guid = gm.guid
    JOIN acore_auth.account a ON a.id = c.account
    LEFT JOIN llm_bot_identities i ON i.bot_guid = c.guid
    WHERE (a.username LIKE 'RNDBOT%%' OR EXISTS (
        SELECT 1 FROM llm_group_bot_traits t WHERE t.bot_guid = c.guid
    ))
    AND EXISTS (
        SELECT 1 FROM llm_guild_chat_sessions s
        JOIN characters p ON p.guid = s.player_guid AND p.online = 1
        JOIN guild_member pm ON pm.guid = p.guid
            AND pm.guildid = s.guild_id
        WHERE s.guild_id = gm.guildid
    )
"""


def prepare_guild_profiles(db, client, config):
    """One page per invocation; caller permits only one outstanding worker.

    Keyset progress advances even after a failed ensure so one broken profile
    cannot monopolize the bounded batch. A later pass retries after its TTL.
    """
    global _last_guid
    if not guild_profiles_enabled(config):
        return 0
    limit = config_int(config, 'LLMChatter.Profile.GuildBatchSize', 2, 1, 100)
    version = config_int(config, 'LLMChatter.Memory.IdentityVersion', 1)
    needs_story = config_int(config, 'LLMChatter.Backstory.Enable', 1)
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute(
            'SELECT c.guid, c.name ' + _ELIGIBLE + """
            AND c.guid > %s
            AND (i.bot_guid IS NULL OR i.identity_version != %s
                OR COALESCE(TRIM(i.trait1), '') = ''
                OR COALESCE(TRIM(i.trait2), '') = ''
                OR COALESCE(TRIM(i.trait3), '') = ''
                OR COALESCE(TRIM(i.tone), '') = ''
                OR (%s AND COALESCE(TRIM(i.backstory), '') = ''))
            ORDER BY c.guid LIMIT %s
            """, (_last_guid, version, needs_story, limit),
        )
        rows = cursor.fetchall()
        if not rows:
            _last_guid = 0
            return 0
        count = 0
        for row in rows:
            _last_guid = int(row['guid'])
            # Another job may have removed the real player or bot membership
            # while earlier profiles in this batch were being generated.
            db.commit()
            cursor.execute('SELECT c.guid ' + _ELIGIBLE + ' AND c.guid=%s',
                           (_last_guid,))
            if cursor.fetchone():
                ensure_bot_profile(db, client, config, _last_guid, row['name'])
                count += 1
        return count
    finally:
        cursor.close()
