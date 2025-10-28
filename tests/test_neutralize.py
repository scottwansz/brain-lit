import unittest

from svc.database import query_by_sql, batch_insert_records, update_table, query_table
from svc.neutralize import neutralize


class TestNeutralize(unittest.TestCase):
    """测试neutralize方法"""
    def test_neutralize(self):

        sql = f"""
        select * from asi_alphas where submitted=1 and sharp>1.58 and fitness>1 and used!='1'
        """

        selected_alphas = query_by_sql( sql)
        # selected_alphas = query_table(table_name, {'submitted': 1})

        # 排除best_alphas中used属性为1的记录
        selected_alphas = [alpha for alpha in selected_alphas if alpha.get('used') != '1']

        print('len(selected_alphas):', len(selected_alphas))

        selected_neutralization_opts = ["SLOW", "FAST", "SLOW_AND_FAST", "CROWDING", "STATISTICAL", "REVERSION_AND_MOMENTUM"]
        new_alphas = neutralize(selected_alphas, selected_neutralization_opts, new_phase=2)

        print('len(new_alphas):', len(new_alphas))

        # 将new_alphas按每200个元素分批处理
        batch_size = 200
        table_name = f"{selected_alphas[0]['region'].lower()}_alphas"

        for i in range(0, len(new_alphas), batch_size):
            batch = new_alphas[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}: {len(batch)} items")

            affected_rows = batch_insert_records(table_name, batch)
            if affected_rows > 0:
                print(f"成功保存 {affected_rows} 条记录到数据库")
            else:
                print("保存到数据库时出错")