-- One outstanding screenshot preflight per explicitly bound account.
-- Server snapshots stay in memory: restart invalidates pending captures.
CREATE TABLE IF NOT EXISTS `llm_screenshot_proximity` (
    `account_id` INT UNSIGNED NOT NULL,
    `request_token` CHAR(32) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    `state` ENUM('requested', 'ready', 'observed', 'consumed') NOT NULL,
    `player_guid` INT UNSIGNED DEFAULT NULL,
    `observation` TEXT DEFAULT NULL,
    `requested_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `expires_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`account_id`),
    UNIQUE KEY `uq_request_token` (`request_token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
