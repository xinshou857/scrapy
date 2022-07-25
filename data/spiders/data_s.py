import datetime
import logging
import os
import sys
import time

import scrapy
import re
import pandas as pd
from sqlalchemy import create_engine
from scrapy import Request
from lxml import etree
import difflib
from scrapy.exceptions import CloseSpider
from data.items import DataItem
import scrapy.signals
import inform

response_dict = {}


class DataSSpider(scrapy.Spider):
    engine = create_engine('mysql+pymysql://root:eQKVR*8742zedu@9.135.131.156:3306/scrapy_data')
    # url_sql = "select * from url_name;"
    # engine = create_engine('mysql+pymysql://root:@127.0.0.1:3306/scrapy_data')

    # url_data = pd.read_sql_query(url_sql, engine).to_dict(orient='records')
    name = 'spider_5173'  # 项目名称
    # allowed_domains = ['https://www.dd373.com/']  # 爬取的网站
    # a = os.environ.get('gameid')
    start_urls = []  # 发起请求的url列表
    message_dict = {}  # 路由信息
    exist_list = []
    game_url = [
        'https://www.jiaoyimao.com/search/all.html',
        'https://game.dd373.com/y-0-0.html',
    ]  # 游戏道具交易总数的获取得url
    # 获取元素配置表所有内容
    all_sql = "select * from parser_config;"
    all_data = pd.read_sql_query(all_sql, engine)
    # 获取配置表拼接url
    # sql = "select * from scrapy_url_config where spider_name = '%s' ;" % name
    sql = "select * from scrapy_url_config;"
    data = pd.read_sql_query(sql, engine).to_dict(orient='records')
    # print(data)

    # 整理配置表当中的数据，将他存储到一个子典当中，需要进行请求得url保存在start_urls
    for i in data:
        sy = re.findall(r'{{(.*?)}}', i['url'])
        for sl in sy:
            # print(i["spider_name"])
            sy_sql = "select name,value from template_variable  where name='%s';" % sl
            df = pd.read_sql_query(sy_sql, engine)
            game_id = df[df["name"] == sl]['value'].tolist()
            # print(game_id)
            sl = "{{" + sl + "}}"
            if len(sy) == 2:
                for id_data in game_id:
                    start_urls.append(i['url'].replace(sl, id_data))
                    message_dict[i['url'].replace(sl, id_data)] = {'parser_config_id': i['parser_config_id'],
                                                                   'yeshu': i['yeshu'], 'match': i['match']}
            # 销售
            else:
                start_urls.append(i['url'])
                message_dict[i['url']] = {'parser_config_id': i['parser_config_id'], 'yeshu': i['yeshu'],
                                          'match': i['match']}

    # 发起多个页面的请求
    def parse(self, response):
        # self.start_requests()
        url_key = []
        data_response = re.findall(r' (.*?)>', str(response))
        for url in self.start_urls:  # 遍历所有需要爬取数据的url进行拼接
            suited = difflib.get_close_matches(data_response[0], list(self.message_dict.keys()),
                                               n=1)  # 匹配message_dict得url
            # print("suited", suited)
            if len(suited) != 0:
                if suited[0] in url_key:
                    continue
                else:
                    url_key += suited
                    url = url_key[0].replace("{{PAGE_NUM}}", "{}")
                    if self.message_dict[url_key[0]]['match'] != None:
                        amount = re.findall(self.message_dict[url_key[0]]['match'],
                                            response.xpath(self.message_dict[url_key[0]]['yeshu']).extract()[0])
                    else:
                        amount = response.xpath(self.message_dict[url_key[0]]['yeshu']).extract()[0]
                    # print(amount)
                    for num_der in range(1, int(amount[0]) + 1):
                        time.sleep(5)
                        yield scrapy.Request(url.format(num_der), dont_filter=True, callback=self.parse_two_page)
        for count in self.game_url:  # 单独对不同游戏的不同商品种类的url发起请求
            if count in self.exist_list:
                continue
            else:
                self.exist_list.append(count)
                time.sleep(5)
                yield scrapy.Request(count, dont_filter=True, callback=self.parse_three_page)

    # 获取配置表当中所需的数据
    def parse_two_page(self, response):
        print(response)
        global response_dict
        data_response = re.findall(r' (.*?)>', str(response))
        data_key = difflib.get_close_matches(data_response[0], list(self.message_dict.keys()), n=1)  # 模糊匹配相对应url
        print("key", data_key)
        item = DataItem()
        # 获取相对应的配置信息
        if len(data_key) != 0:
            try:
                for value in self.all_data.to_dict(orient='records'):
                    if value['parser_config_id'] == self.message_dict[data_key[0]]['parser_config_id']:
                        response_dict = value

                    if bool(response_dict):
                        content = \
                        self.all_data[(self.all_data['parser_config_id'] == response_dict['parser_config_id']) & (
                                self.all_data['name'] == 'title')]['source'].tolist()
                        num = len(response.xpath(content[0]).extract())  # 获取当前页数据的条数
                        name = response_dict['name']
                        item[name] = []
                        # 根据配置表获取相对应的数据
                        if response_dict['source'] != '':
                            if response_dict['matching'] == '':
                                item[name] += response.xpath(response_dict['source']).extract()
                            else:
                                # if name == 'date_time':
                                #     now_time = datetime.datetime.now()
                                #     item[name].append(now_time.strftime('%Y-%m-%d %H:%M:%S'))
                                # if name == 'data_type':  # 将数据分类
                                #     num = len(item['title'])
                                #     for i in range(num):
                                #         if self.message_dict[data_key[0]] == 2:
                                #             item[name].append(1)
                                #         else:
                                #             item[name].append(0)
                                # else:
                                # 获取相对应的物品单价，没有则添加为空
                                if name == 'unit_price':
                                    for degree in range(1, num + 1):
                                        unit_data = response.xpath(response_dict['source'] % degree).extract()  #
                                        if len(unit_data) == 0:
                                            item[name].append(None)
                                        else:

                                            item[name].append(
                                                re.findall(response_dict['matching'], unit_data[0])[0].strip())
                                else:
                                    for re_value in response.xpath(response_dict['source']).extract():
                                        if '\n' in re_value:
                                            item[name].append((re_value.split('\n')[-2]).strip())
                                        else:
                                            item_data = \
                                                '/'.join(re.findall(response_dict['matching'], re_value)).split('>')[-1]
                                            if item_data != '':
                                                item[name].append(item_data)
                        else:
                            if name == 'date_time':  # 抓取时间
                                now_time = datetime.datetime.now()
                                for i in range(num):
                                    item[name].append(now_time.strftime('%Y-%m-%d %H:%M:%S'))
                            elif name == 'data_type':  # 将数据分类
                                for i in range(num):
                                    if self.message_dict[data_key[0]]['parser_config_id'] == 2:
                                        item[name].append(1)
                                    else:
                                        item[name].append(0)
                            elif name == 'derivation':  # 数据来源
                                for i in range(num):
                                    item[name].append(data_response[0].split('/')[2])
                            else:
                                for i in range(num):
                                    item[name].append(None)
            except Exception as e:
                error_data = "%s网站%s出现异常，报错信息为%s" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), response, e)
                parse_error(error_data)
        print("//////////////////////", item)
        return item

    # 对交易猫和dd373各个游戏进行请求
    def parse_three_page(self, response):
        exist_response = re.findall(r' (.*?)>', str(response))
        exit_list = exist_response[0].split('/')
        print(exit_list)
        if "jiaoyimao" in exit_list[2]:
            next_url = response.xpath('//div[@id="scrollMain"]/div[1]/ul/li/div[1]/a/@href').extract()
            if len(next_url) != 0:
                for loop in next_url:
                    # exit_url = exit_list[0] + "//" + exit_list[2] + loop
                    yield scrapy.Request(loop, dont_filter=True, callback=self.parse_four_page)
        elif "dd373" in exit_list[2]:
            next_url = response.xpath('//div[@class="game-list-box clearfix"]/ul/li/a/@href').extract()
            if len(next_url) != 0:
                for loop in next_url:
                    exit_url = exit_list[0] + loop
                    time.sleep(5)
                    yield scrapy.Request(exit_url, dont_filter=True, callback=self.parse_four_page)
        # print("11111",next_url)

    # 对各个游戏不同得商品进行请求
    def parse_four_page(self, response):
        following_response = re.findall(r' (.*?)>', str(response))
        following_list = following_response[0].split('/')

        if "jiaoyimao" in following_list[2]:
            following_url = response.xpath('//div[@class="bd"]/div[1]/div/span/a/@href').extract()
            if len(following_url) != 0:
                for loop in following_url:
                    yield scrapy.Request(loop, dont_filter=True, callback=self.parse_five_page)
        elif "dd373" in following_list[2]:
            following_url = response.xpath('/html/body/div[2]/div[2]/div/div[3]/div[1]/div[2]/a/@href').extract()
            if len(following_url) != 0:
                following_url.pop()
                for loop in following_url:
                    following_url = following_list[0] + "//" + following_list[2] + loop
                    yield scrapy.Request(following_url, dont_filter=True, callback=self.parse_five_page)
        # print("11111",next_url)

    # 获取各个商品得数据
    def parse_five_page(self, response):
        print("kkkkkkkkk", response)
        five_response = re.findall(r' (.*?)>', str(response))
        five_list = five_response[0].split('/')
        print(five_list)
        item = DataItem()
        try:
            if "jiaoyimao" in five_list[2]:
                item['game_name'] = re.findall(">(.*?)</a>",
                                               response.xpath('//div[@class="wrap"]/div[1]/a[3]').extract()[0])

                item['num_data'] = re.findall(">(.*?)</span>",
                                              response.xpath(
                                                  '//div[@class="wrap"]/div[3]/div[1]/div[1]/span').extract()[0])

                if len(response.xpath('//div[@class="wrap"]/div[1]/a[4]').extract()) != 0:
                    item['prop_name'] = re.findall(">(.*?)</a>", response.xpath(
                        '//div[@class="wrap"]/div[1]/a[4]').extract()[0])
                else:
                    item['prop_name'] = ['全部']
                item['derivation'] = [five_list[2]]
            elif "dd373" in five_list[2]:
                item['game_name'] = re.findall(">(.*?)</p>",
                                               response.xpath('//*[@id="topAdLink"]/div/div[1]/div/p[1]').extract()[0])

                item['num_data'] = re.findall(">(.*?)</span>",
                                              response.xpath(
                                                  '//div[@class="current-right-box"]/a/h1/span[2]').extract()[0])

                item['prop_name'] = re.findall(">(.*?)</a>",
                                               response.xpath(
                                                   '//div[@class="goods-select-value"]/a[@class="active"]').extract()[
                                                   0])
                item['derivation'] = [five_list[2]]
            item['date_time'] = [datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
        except Exception as e:
            error_data = "%s网站%s出现异常，报错信息为%s" % (datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), response, e)
            parse_error(error_data)
        print(item)
        return item

    engine.dispose()


def parse_error(error_data):
    msg = inform.Tof4RTX()
    msg.sender = "v_yliyuan",  # 发件人
    msg.receiver = "v_yliyuan,shaoyouwang",  # 收件人
    msg.headline = "test001",  # 标题
    msg.msginfo = error_data
    print(error_data)
    msg.Title = 'TOF4_msg_SendRTXInfo_test'
    msg.Content = "TOF4_msg_SendRTXInfo_test"
    msg.From = 'disyli'
    msg.To = 'disyli'

    # 实例化一个Mykey()对象为key
    key = inform.MyKey()
    key.Paasid = 'bglhbnhpihzfewxpexvhbg'
    key.Token = 'r3RRvBI0Wmk7ScMjCItZUmpJ6Dhy60zd'

    # send
    max_retries = 3
    msg.Send(URL=inform.URL, Mykey=key, Max_retries=max_retries)
