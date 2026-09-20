/*
 * mod-llm-chatter - demand-driven ambient trade inventory snapshots
 */

#include "LLMChatterTrade.h"

#include "Bag.h"
#include "Item.h"
#include "LLMChatterConfig.h"
#include "Player.h"
#include "Random.h"

#include <algorithm>
#include <utility>

namespace
{
bool IsEligibleTradeItem(Item* item)
{
    if (!item || !item->IsInWorld())
        return false;

    ItemTemplate const* itemTemplate = item->GetTemplate();
    if (!itemTemplate || !item->GetCount())
        return false;

    if (item->IsBag()
        || itemTemplate->Class == ITEM_CLASS_CONTAINER)
        return false;

    if (!item->CanBeTraded() || item->IsWrapped())
        return false;

    if (itemTemplate->HasFlag(ITEM_FLAG_CONJURED)
        || itemTemplate->Class == ITEM_CLASS_QUEST
        || itemTemplate->Duration > 0
        || itemTemplate->Quality < ITEM_QUALITY_NORMAL)
        return false;

    return true;
}

uint32 GetTradeItemSelectionWeight(ItemTemplate const* itemTemplate)
{
    uint32 quality = std::clamp<uint32>(
        itemTemplate->Quality, ITEM_QUALITY_NORMAL,
        MAX_ITEM_QUALITY - 1);
    uint32 qualitySteps = quality - ITEM_QUALITY_NORMAL;
    return 1 + qualitySteps
        * sLLMChatterConfig->_ambientTradeQualityWeightBonus;
}

void ConsiderTradeItem(
    Item* item, uint32& totalWeight,
    std::optional<ChatterTradeItemSnapshot>& selected)
{
    if (!IsEligibleTradeItem(item))
        return;

    ItemTemplate const* itemTemplate = item->GetTemplate();
    uint32 itemWeight = GetTradeItemSelectionWeight(itemTemplate);
    totalWeight += itemWeight;
    if (urand(1, totalWeight) > itemWeight)
        return;

    ChatterTradeItemSnapshot snapshot;
    snapshot.itemInstanceGuid = item->GetGUID().GetCounter();
    snapshot.itemEntry = item->GetEntry();
    snapshot.itemName = itemTemplate->Name1;
    snapshot.quality = itemTemplate->Quality;
    snapshot.count = item->GetCount();
    snapshot.sellPrice = itemTemplate->SellPrice;
    snapshot.allowableClass = itemTemplate->AllowableClass;
    snapshot.requiredLevel = itemTemplate->RequiredLevel;
    snapshot.randomPropertyId =
        item->GetItemRandomPropertyId();
    snapshot.suffixFactor = item->GetItemSuffixFactor();
    selected = std::move(snapshot);
}
}

std::optional<ChatterTradeItemSnapshot>
SelectChatterTradeItem(Player* seller)
{
    if (!seller || !seller->IsInWorld())
        return std::nullopt;

    std::optional<ChatterTradeItemSnapshot> selected;
    uint32 totalWeight = 0;

    for (uint8 slot = INVENTORY_SLOT_ITEM_START;
         slot < INVENTORY_SLOT_ITEM_END; ++slot)
    {
        ConsiderTradeItem(
            seller->GetItemByPos(INVENTORY_SLOT_BAG_0, slot),
            totalWeight, selected);
    }

    for (uint8 bagSlot = INVENTORY_SLOT_BAG_START;
         bagSlot < INVENTORY_SLOT_BAG_END; ++bagSlot)
    {
        Bag* bag = seller->GetBagByPos(bagSlot);
        if (!bag)
            continue;

        for (uint8 slot = 0; slot < bag->GetBagSize(); ++slot)
        {
            ConsiderTradeItem(
                bag->GetItemByPos(slot),
                totalWeight, selected);
        }
    }

    return selected;
}
