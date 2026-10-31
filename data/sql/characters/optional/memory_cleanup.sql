-- Optional cleanup of bot memories written before the 2026-10-28 memory
-- fixes. NEVER applied automatically.
--
-- It removes memories that break immersion or can no longer be trusted:
--   * rows longer than 400 characters (over the memory length limit);
--   * rows naming game mechanics: "achievement", "level <number>", "quest";
--   * rows starting with "Today"/"today" (they read as new when recalled
--     weeks later);
--   * pending rows (active = 0) older than one day, left by sessions that
--     never settled.
-- first_meeting memories are never touched.
--
-- Usage:
--   1. Back up the table first:
--        mysqldump -uroot -p acore_characters llm_bot_memories > memories.sql
--   2. Run the PREVIEW part below and read the counts.
--   3. Run the whole file:
--        mysql -uroot -p acore_characters < memory_cleanup.sql

-- ---------------------------------------------------------------- PREVIEW
SELECT
    SUM(CHAR_LENGTH(memory) > 400)                    AS too_long,
    SUM(memory REGEXP '(^|[^[:alpha:]])achievement')  AS achievement,
    SUM(memory REGEXP '(^|[^[:alpha:]])level [0-9]+') AS level_number,
    SUM(memory REGEXP '(^|[^[:alpha:]])quest')        AS quest,
    SUM(memory REGEXP '^[Tt]oday')                    AS today,
    SUM(active = 0 AND created_at < NOW() - INTERVAL 1 DAY) AS stale_pending
FROM llm_bot_memories
WHERE memory_type != 'first_meeting';

-- ----------------------------------------------------------------- DELETE
DELETE FROM llm_bot_memories
WHERE memory_type != 'first_meeting'
  AND (
        CHAR_LENGTH(memory) > 400
     OR memory REGEXP '(^|[^[:alpha:]])achievement'
     OR memory REGEXP '(^|[^[:alpha:]])level [0-9]+'
     OR memory REGEXP '(^|[^[:alpha:]])quest'
     OR memory REGEXP '^[Tt]oday'
     OR (active = 0 AND created_at < NOW() - INTERVAL 1 DAY)
  );
