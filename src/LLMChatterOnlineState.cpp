/*
 * mod-llm-chatter - per-character online flag on logout
 */

#include "LLMChatterOnlineState.h"

#include "DatabaseEnv.h"
#include "LLMChatterConfig.h"
#include "ObjectGuid.h"
#include "ScriptMgr.h"

// On logout the core marks every character of the account offline.
// That fits one character per account, but playerbots log in under
// shared accounts: an alt bot uses its owner's account and random bots
// share theirs. One bot logging out would flag the real player, or the
// other bots of the account, offline while they are still in the
// world, and the bridge would treat the realm as empty.
class LLMChatterOnlineStatePlayerScript : public PlayerScript
{
public:
    LLMChatterOnlineStatePlayerScript()
        : PlayerScript("LLMChatterOnlineStatePlayerScript",
              {PLAYERHOOK_CAN_MARK_ACCOUNT_OFFLINE})
    {
    }

    bool OnPlayerCanMarkAccountOffline(
        ObjectGuid guid, uint32 /*accountId*/) override
    {
        if (!sLLMChatterConfig->IsEnabled())
            return true;

        // Only the character that left goes offline. For an account
        // with a single character in the world this equals the core's
        // account-wide update.
        CharacterDatabase.Execute(
            "UPDATE characters SET online = 0 WHERE guid = {}",
            guid.GetCounter());
        return false;
    }
};

void AddLLMChatterOnlineStateScripts()
{
    new LLMChatterOnlineStatePlayerScript();
}
