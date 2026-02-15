-- Pre-cached LLM responses for instant combat delivery
CREATE TABLE IF NOT EXISTS `llm_group_cached_responses` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `group_id` INT UNSIGNED NOT NULL,
    `bot_guid` INT UNSIGNED NOT NULL,
    `event_category` VARCHAR(48) NOT NULL,
    `message` VARCHAR(255) NOT NULL,
    `emote` VARCHAR(32) DEFAULT NULL,
    `status` ENUM('ready','used','expired') NOT NULL DEFAULT 'ready',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `expires_at` TIMESTAMP NULL DEFAULT NULL,
    `used_at` TIMESTAMP NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    KEY `idx_lookup` (`group_id`, `bot_guid`, `event_category`, `status`, `created_at`),
    KEY `idx_expiry` (`status`, `expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
