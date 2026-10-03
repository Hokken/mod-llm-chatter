-- Open-world PvP reactions: Guild kill comments and Guild or General
-- death reactions.
-- Appends only the missing values to whatever the column already holds,
-- so this file can run before or after other event-type migrations.

SET @event_type = (
  SELECT COLUMN_TYPE FROM information_schema.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'llm_chatter_events'
    AND COLUMN_NAME = 'event_type'
);

SET @add_values = CONCAT_WS(',',
  IF(@event_type LIKE '%''guild_pvp_kill''%', NULL, '''guild_pvp_kill'''),
  IF(@event_type LIKE '%''guild_pvp_death''%', NULL, '''guild_pvp_death'''),
  IF(@event_type LIKE '%''zone_pvp_death''%', NULL, '''zone_pvp_death''')
);

SET @sql = IF(
  @event_type IS NULL OR @add_values = '',
  'SELECT 1',
  CONCAT(
    'ALTER TABLE `llm_chatter_events` MODIFY COLUMN `event_type` ',
    LEFT(@event_type, CHAR_LENGTH(@event_type) - 1),
    ',', @add_values, ') NOT NULL'
  )
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
