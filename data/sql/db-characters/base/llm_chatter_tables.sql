-- LLM Chatter Module Tables
-- Dynamic bot conversations powered by AI

-- Queue for chatter requests (sent to Python bridge)
DROP TABLE IF EXISTS `llm_chatter_queue`;
CREATE TABLE `llm_chatter_queue` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `request_type` ENUM('statement', 'conversation') NOT NULL DEFAULT 'statement',
    `bot1_guid` INT UNSIGNED NOT NULL,
    `bot1_name` VARCHAR(64) NOT NULL,
    `bot1_class` VARCHAR(32) NOT NULL,
    `bot1_race` VARCHAR(32) NOT NULL,
    `bot1_level` TINYINT UNSIGNED NOT NULL,
    `bot1_zone` VARCHAR(128) NOT NULL,
    `bot2_guid` INT UNSIGNED DEFAULT NULL,
    `bot2_name` VARCHAR(64) DEFAULT NULL,
    `bot2_class` VARCHAR(32) DEFAULT NULL,
    `bot2_race` VARCHAR(32) DEFAULT NULL,
    `bot2_level` TINYINT UNSIGNED DEFAULT NULL,
    `status` ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `processed_at` TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_status` (`status`),
    KEY `idx_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Messages to be delivered (from completed requests)
DROP TABLE IF EXISTS `llm_chatter_messages`;
CREATE TABLE `llm_chatter_messages` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `queue_id` INT UNSIGNED NOT NULL,
    `sequence` TINYINT UNSIGNED NOT NULL DEFAULT 0,
    `bot_guid` INT UNSIGNED NOT NULL,
    `bot_name` VARCHAR(64) NOT NULL,
    `message` TEXT NOT NULL,
    `channel` VARCHAR(32) NOT NULL DEFAULT 'general',
    `delivered` TINYINT(1) NOT NULL DEFAULT 0,
    `deliver_at` TIMESTAMP NULL DEFAULT NULL,
    `delivered_at` TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_queue` (`queue_id`),
    KEY `idx_delivery` (`delivered`, `deliver_at`),
    CONSTRAINT `fk_chatter_queue` FOREIGN KEY (`queue_id`)
        REFERENCES `llm_chatter_queue` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
