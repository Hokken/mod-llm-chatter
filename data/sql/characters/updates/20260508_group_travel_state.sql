-- Live travel state for party bots.

SET @has_travel_mode := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'travel_mode'
);
SET @sql := IF(
    @has_travel_mode = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `travel_mode` VARCHAR(32) DEFAULT NULL
       AFTER `map`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_travel_context := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'travel_context'
);
SET @sql := IF(
    @has_travel_context = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `travel_context` VARCHAR(512) DEFAULT NULL
       AFTER `travel_mode`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_is_mounted := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'is_mounted'
);
SET @sql := IF(
    @has_is_mounted = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `is_mounted` TINYINT(1) NOT NULL DEFAULT 0
       AFTER `travel_context`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_is_flying := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'is_flying'
);
SET @sql := IF(
    @has_is_flying = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `is_flying` TINYINT(1) NOT NULL DEFAULT 0
       AFTER `is_mounted`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_is_taxi := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'is_taxi_flying'
);
SET @sql := IF(
    @has_is_taxi = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `is_taxi_flying`
           TINYINT(1) NOT NULL DEFAULT 0
       AFTER `is_flying`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_is_transport := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'is_on_transport'
);
SET @sql := IF(
    @has_is_transport = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `is_on_transport`
           TINYINT(1) NOT NULL DEFAULT 0
       AFTER `is_taxi_flying`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_mount_display := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'mount_display_id'
);
SET @sql := IF(
    @has_mount_display = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `mount_display_id`
           INT UNSIGNED NOT NULL DEFAULT 0
       AFTER `is_on_transport`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_transport_name := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'transport_name'
);
SET @sql := IF(
    @has_transport_name = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `transport_name` VARCHAR(128) DEFAULT NULL
       AFTER `mount_display_id`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @has_travel_updated := (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'llm_group_bot_traits'
      AND COLUMN_NAME = 'travel_updated_at'
);
SET @sql := IF(
    @has_travel_updated = 0,
    'ALTER TABLE `llm_group_bot_traits`
       ADD COLUMN `travel_updated_at` TIMESTAMP NULL DEFAULT NULL
       AFTER `transport_name`',
    'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
