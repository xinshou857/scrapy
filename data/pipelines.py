# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import random
import string
import time

from sqlalchemy import create_engine
import pandas as pd
from itemadapter import ItemAdapter
from scrapy.utils.project import get_project_settings
import pymysql


df_data2 = 0


class DataPipeline:
    # 标记重复数据
    def function(self, dict_son):
        # if len(dict_son.index.tolist()) > 2:
        temp = dict_son[['title', 'price', 'game_area', 'type_merchandize', 'num_data', 'unit_price', 'gather_time',
                         'data_type']].to_dict()
        if temp in df_data2:
            return 1

    def process_item(self, item, spider):
        global df_data2
        engine = create_engine('mysql+pymysql://root:eQKVR*8742zedu@9.135.131.156:3306/scrapy_data')  # 数据库连接
        # engine = create_engine('mysql+pymysql://root:@127.0.0.1:3306/scrapy_data')
        item_sql = 'select * from design;'
        item_df = pd.read_sql_query(item_sql, engine)  # 获取已经存在的数据
        del item_df['id']
        if len(item) > 5:
            df_data2 = item_df[
                ['title', 'price', 'game_area', 'type_merchandize', 'num_data', 'unit_price', 'gather_time',
                 'data_type']].to_dict("records")
            # print("=======================", df_data2)
            df = pd.DataFrame.from_dict(item, orient='index').T  # 将json转换为dataframe
            df = df.drop_duplicates()  # 去除当前item的重复数据
            df['标记'] = df.apply(lambda x: self.function(x), axis=1)  # 将与数据库的数据比较，重复的标记为1
            df = df[~df['标记'].isin([1.0])]  # 删除标记为1.0的数据
            del df['标记']  # 删除标记这一列
            df.to_sql('design', engine, index=False, if_exists='append')
        else:
            time.sleep(5)
            total_data = pd.DataFrame.from_dict(item, orient='index').T  # 将json转换为dataframe
            print("000000000000000000", total_data)
            total_data.to_sql('sum_design', engine, index=False, if_exists='append')

        a_sql = 'delete from scrapy_data.design where id not in (select t.id from (select min(id) AS id from scrapy_data.design  group by title, price, game_area, type_merchandize, num_data, unit_price , gather_time,data_type)t )'
        all_data = pd.read_sql(a_sql, engine)
        engine.dispose()  # 断开数据库
