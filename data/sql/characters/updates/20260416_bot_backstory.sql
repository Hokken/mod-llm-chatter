-- Add backstory column to session-scoped bot traits
-- (idempotent — skips if column already exists)
SET @dbname = DATABASE();
SET @tablename = 'llm_group_bot_traits';
SET @columnname = 'backstory';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @dbname
     AND TABLE_NAME = @tablename
     AND COLUMN_NAME = @columnname) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE `', @tablename,
         '` ADD COLUMN `', @columnname,
         '` TEXT DEFAULT NULL AFTER `farewell_msg`')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add backstory column to persistent bot identities
SET @tablename = 'llm_bot_identities';
SET @preparedStatement = (SELECT IF(
  (SELECT COUNT(*) FROM information_schema.COLUMNS
   WHERE TABLE_SCHEMA = @dbname
     AND TABLE_NAME = @tablename
     AND COLUMN_NAME = @columnname) > 0,
  'SELECT 1',
  CONCAT('ALTER TABLE `', @tablename,
         '` ADD COLUMN `', @columnname,
         '` TEXT DEFAULT NULL AFTER `farewell_msg`')
));
PREPARE alterIfNotExists FROM @preparedStatement;
EXECUTE alterIfNotExists;
DEALLOCATE PREPARE alterIfNotExists;

-- Add bot_backstory_regen event type
-- (MODIFY COLUMN is idempotent — safe to rerun)
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
    'bot_group_aggro_loss',
    'bot_group_quest_accept',
    'bot_group_quest_accept_batch',
    'weather_ambient',
    'bot_group_nearby_object',
    'bot_group_join_batch',
    'bg_match_start',
    'bg_match_end',
    'bg_pvp_kill',
    'bg_flag_picked_up',
    'bg_flag_dropped',
    'bg_flag_captured',
    'bg_flag_returned',
    'bg_node_contested',
    'bg_node_captured',
    'bg_score_milestone',
    'bg_idle_chatter',
    'bg_player_arrival',
    'raid_boss_pull',
    'raid_boss_kill',
    'raid_boss_wipe',
    'raid_idle_morale',
    'bot_group_farewell',
    'bot_group_subzone_change',
    'bot_group_emote_observer',
    'bot_group_emote_reaction',
    'bot_group_screenshot_observation',
    'proximity_say',
    'proximity_conversation',
    'proximity_reply',
    'proximity_player_say',
    'proximity_player_conversation',
    'bot_backstory_regen'
  ) NOT NULL;
