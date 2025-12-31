select * from :'USA_alphas' where sharp < -1 and simulated = 1 order by sharp ;
update :'USA_alphas' set simulated = 0, alpha = concat('-', alpha), phase = 2 where sharp < -1 and simulated = 1;
select * from :'USA_alphas' where phase = 2 and simulated = 1 order by sharp desc ;
update :'USA_alphas' set phase = 1 where phase = 2 and simulated = 1;
# update ASI_alphas set simulated = 0, phase = 4 where phase = 3 and simulated = 0 and updated_at >= '2025-06-28' ;
select * from :'USA_alphas' where phase = 3 and simulated = 0 and updated_at >= '2025-06-28' ;

select phase, category, dataset, simulated, count(*)
from USA_alphas
group by category, dataset, simulated, phase
order by phase, simulated, category, dataset;

SELECT *,
       ROW_NUMBER() OVER (
           PARTITION BY name
           ORDER BY abs(sharp*fitness) DESC
       ) AS rn
FROM ASI_alphas
where simulated = 1
and passed = 1
order by rn;

WITH ranked_alphas AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY name
               ORDER BY abs(sharp*fitness) DESC
           ) AS rn
    FROM ASI_alphas
    WHERE
#         category = 'earnings' AND
#         dataset = 'earnings4' AND
#         phase = 1 AND
        simulated = 1
)
SELECT * FROM ranked_alphas WHERE rn = 1 AND passed = 0 AND sharp >= 1 ORDER BY abs(sharp*fitness) DESC
# update ASI_alphas SET simulated = 0, passed = 0 WHERE (id) IN (
#     SELECT id FROM ranked_alphas WHERE rn = 1
# )
;

-- 如果需要删除其他记录（保留最高abs(sharp*fitness)）
WITH ranked_alphas AS (
    SELECT *,
           ROW_NUMBER() OVER (
               PARTITION BY name
               ORDER BY abs(sharp*fitness) DESC
           ) AS rn
    FROM :ind_alphas
    WHERE phase = 1 AND simulated = 1 AND delay = 1 and template='ts_basic'
)
DELETE FROM :ind_alphas
WHERE (id) NOT IN (SELECT id FROM ranked_alphas WHERE rn = 1)
AND phase = 1 AND simulated = 1 AND delay = 1 and template='ts_basic';

select * from CHN_alphas
where JSON_CONTAINS(fail_reasons,'[{"name": "D0_SUBMISSION", "limit": 30, "value": 30, "result": "FAIL"}]') ;

SELECT * FROM ind_alphas
WHERE JSON_SEARCH(fail_reasons, 'one', 'CONCENTRATED_WEIGHT', NULL, '$[*].name') IS NOT NULL
  AND JSON_LENGTH(fail_reasons) = 1 AND passed=-1;

update ind_alphas set phase=2, simulated=0
WHERE JSON_SEARCH(fail_reasons, 'one', 'CONCENTRATED_WEIGHT', NULL, '$[*].name') IS NOT NULL
  AND JSON_LENGTH(fail_reasons) = 1 AND passed=-1;