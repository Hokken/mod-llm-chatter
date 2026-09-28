#ifndef MOD_LLM_CHATTER_TRADE_H
#define MOD_LLM_CHATTER_TRADE_H

#include "Define.h"

#include <optional>
#include <string>

class Player;

struct ChatterTradeItemSnapshot
{
    uint32 itemInstanceGuid = 0;
    uint32 itemEntry = 0;
    std::string itemName;
    uint8 quality = 0;
    uint32 count = 0;
    uint32 sellPrice = 0;
    int32 allowableClass = -1;
    uint32 requiredLevel = 0;
    int32 randomPropertyId = 0;
    uint32 suffixFactor = 0;
};

std::optional<ChatterTradeItemSnapshot>
SelectChatterTradeItem(Player* seller);

#endif
