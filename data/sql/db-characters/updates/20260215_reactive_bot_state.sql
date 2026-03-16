-- --------------------------------------------------------
-- Reactive Bot State - Phase 2
-- Adds role column to traits, 3 new event types
-- --------------------------------------------------------

-- Add role column to bot traits table (idempotent)
DROP PROCEDURE IF EXISTS `add_role_column`;
DELIMITER //
CREATE PROCEDURE `add_role_column`()
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = 'llm_group_bot_traits'
          AND COLUMN_NAME = 'role'
    ) THEN
        ALTER TABLE `llm_group_bot_traits`
            ADD COLUMN `role` VARCHAR(16)
            DEFAULT NULL AFTER `trait3`;
    END IF;
END //
DELIMITER ;
CALL `add_role_column`();
DROP PROCEDURE IF EXISTS `add_role_column`;

-- Add 3 new state-triggered event types
ALTER TABLE `llm_chatter_events`
    MODIFY COLUMN `event_type` ENUM(
        'weather_change',
        'holiday_start',
        'holiday_end',
        'creature_death_boss',
        'creature_death_rare',
        'creature_death_guard',
        'player_enters_zone',
        'bot_pvp_kill',
        'bot_level_up',
        'bot_achievement',
        'bot_quest_complete',
        'world_boss_spawn',
        'rare_spawn',
        'transport_arrives',
        'day_night_transition',
        'enemy_player_near',
        'bot_loot_item',
        'bot_group_join',
        'bot_group_kill',
        'bot_group_death',
        'bot_group_loot',
        'bot_group_player_msg',
        'bot_group_combat',
        'bot_group_levelup',
        'bot_group_quest_complete',
        'bot_group_achievement',
        'bot_group_spell_cast',
        'bot_group_quest_objectives',
        'bot_group_resurrect',
        'bot_group_zone_transition',
        'bot_group_dungeon_entry',
        'bot_group_wipe',
        'bot_group_corpse_run',
        'player_general_msg',
        'minor_event',
        'bot_group_low_health',
        'bot_group_oom',
        'bot_group_aggro_loss'
    ) NOT NULL;
