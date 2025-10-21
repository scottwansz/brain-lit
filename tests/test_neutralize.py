import unittest

from brain_lit.svc.database import query_table, query_by_sql, batch_insert_records


class TestNeutralize(unittest.TestCase):
    """测试neutralize方法"""
    def test_neutralize(self):
        """测试neutralize方法"""
        # 创建一个测试数据
        table_name = 'eur_alphas'

        sql = f"""
        WITH ranked_alphas AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY name
                       ORDER BY abs(sharp*fitness) DESC
                   ) AS rn
            FROM {table_name}
            WHERE phase = 1 AND simulated = 1 AND sharp > 1 and fitness >0.8
        )
        select * from ranked_alphas where rn = 1
        """

        # selected_alphas = query_table(table_name, {'passed': 1})
        selected_alphas = query_by_sql( sql)

        print('len(selected_alphas):', len(selected_alphas))

        new_alphas = []
        selected_neutralization_opts = ["SLOW", "FAST", "SLOW_AND_FAST", "CROWDING", "STATISTICAL", "REVERSION_AND_MOMENTUM"]
        for alpha in selected_alphas:
            for neutralization in selected_neutralization_opts:
                # 从原始alpha中选择一部分属性来创建新的alpha
                new_alpha = {
                    'region': alpha.get('region'),
                    'universe': alpha.get('universe'),
                    'delay': alpha.get('delay'),
                    'alpha': alpha.get('alpha'),
                    'decay': alpha.get('decay'),
                    'name': alpha.get('name'),
                    'category': alpha.get('category'),
                    'dataset': alpha.get('dataset'),
                    'neutralization': neutralization,
                    'phase': 2,
                    'simulated': 0,
                }
                new_alphas.append(new_alpha)

        print('len(new_alphas):', len(new_alphas))
        
        # 将new_alphas按每200个元素分批处理
        batch_size = 200
        for i in range(0, len(new_alphas), batch_size):
            batch = new_alphas[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}: {len(batch)} items")
            # for j in range(len(batch)):
            #     print(batch[j])

            affected_rows = batch_insert_records(table_name, batch)
            if affected_rows > 0:
                print(f"成功保存 {affected_rows} 条记录到数据库")
            else:
                print("保存到数据库时出错")