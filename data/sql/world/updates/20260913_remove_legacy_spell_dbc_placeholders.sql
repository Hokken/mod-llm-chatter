-- Remove incomplete spell_dbc overrides created by mod-llm-chatter
-- versions before 2026-04-09. Those versions inserted only ID and
-- Name_Lang_enUS for rank-one talent spells. Because spell_dbc rows
-- replace complete client DBC records, the default-valued fields hid
-- the real spell effects and caused SpellScript validation warnings.
--
-- The gameplay-field checks preserve any complete override that another
-- module or administrator may have supplied for the same spell IDs.
DELETE `sd`
FROM `spell_dbc` AS `sd`
INNER JOIN `talent_dbc` AS `td`
    ON `td`.`SpellRank_1` = `sd`.`ID`
WHERE `td`.`SpellRank_1` <> 0
  AND `sd`.`Category` = 0
  AND `sd`.`DispelType` = 0
  AND `sd`.`Mechanic` = 0
  AND `sd`.`Attributes` = 0
  AND `sd`.`AttributesEx` = 0
  AND `sd`.`AttributesEx2` = 0
  AND `sd`.`AttributesEx3` = 0
  AND `sd`.`AttributesEx4` = 0
  AND `sd`.`AttributesEx5` = 0
  AND `sd`.`AttributesEx6` = 0
  AND `sd`.`AttributesEx7` = 0
  AND `sd`.`ProcTypeMask` = 0
  AND `sd`.`Effect_1` = 0
  AND `sd`.`Effect_2` = 0
  AND `sd`.`Effect_3` = 0
  AND `sd`.`EffectAura_1` = 0
  AND `sd`.`EffectAura_2` = 0
  AND `sd`.`EffectAura_3` = 0
  AND `sd`.`SpellClassSet` = 0
  AND `sd`.`SpellClassMask_1` = 0
  AND `sd`.`SpellClassMask_2` = 0
  AND `sd`.`SpellClassMask_3` = 0;
