-- Persistent private player/bot conversation transcript.
CREATE TABLE IF NOT EXISTS `llm_whisper_history` (
    `id` INT UNSIGNED NOT NULL AUTO_INCREMENT,
    `player_guid` INT UNSIGNED NOT NULL,
    `bot_guid` INT UNSIGNED NOT NULL,
    `speaker_guid` INT UNSIGNED NOT NULL,
    `is_bot` TINYINT(1) NOT NULL DEFAULT 0,
    `message` TEXT NOT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `idx_player_bot_id` (`player_guid`, `bot_guid`, `id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
