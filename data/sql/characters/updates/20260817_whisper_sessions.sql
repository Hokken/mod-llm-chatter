-- Ordered private player/bot conversations.  A new player line advances the
-- turn so stale asynchronous replies can be discarded safely.
CREATE TABLE IF NOT EXISTS `llm_whisper_sessions` (
    `player_guid` INT UNSIGNED NOT NULL,
    `bot_guid` INT UNSIGNED NOT NULL,
    `turn_id` INT UNSIGNED NOT NULL DEFAULT 0,
    `last_activity_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`player_guid`, `bot_guid`),
    KEY `idx_last_activity` (`last_activity_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `llm_whisper_history`
    ADD KEY `idx_player_bot_created` (`player_guid`, `bot_guid`, `created_at`);
