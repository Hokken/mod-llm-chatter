-- Race names as the worldserver knows them, rewritten at every startup.
-- The bridge reads them for races outside the original ten (ChrRaces).

CREATE TABLE IF NOT EXISTS `llm_chatter_race_names` (
  `race_id` TINYINT UNSIGNED NOT NULL,
  `name` VARCHAR(64) NOT NULL,
  PRIMARY KEY (`race_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
