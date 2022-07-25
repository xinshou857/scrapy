# !/usr/bin/python
# -*- coding: UTF-8 -*-
import hashlib
import requests as req
import time
import random
from urllib3.util.retry import Retry
import json
from requests.adapters import HTTPAdapter


# tof4_header的签名生成.签名方式说明:http://rio.tencent.com/product?appname=服务开发&amp;path=%2Fhtml%2F开发者中心%2F1.服务开发%2F2.开发指南%2F1.接口调用指南%2F接口调用指南.html
def tof4_sign(timestamp, token, nonce):
    # 实例化一个hashlib.sha256()对象
    x = hashlib.sha256()
    # 将几个独特的特征拼接成一个字符串
    string = timestamp + token + nonce + timestamp
    # 以默认方式(utf-8)编码字符串加入x达到混淆目的
    x.update(string.encode())
    # 256位的认证码以16进制的字符串显示(upper() 方法将字符串中的小写字母转为大写字母。)
    return x.hexdigest().upper()


# 类MyKey()
class MyKey():
    # 类MyKey()的构造函数, paasid和token都是只有headers处用到的
    def __init__(self):
        # paasid
        self.Paasid = ''
        # paasid对应的生产token
        self.Token = ''


# 类Tof4RTX()
class Tof4RTX():
    def __init__(self):
        self.From = ''
        self.To = ''
        self.Title = ''
        self.Content = ''
        self.sender = '',  # 发件人
        self.receiver = '',  # 收件人
        self.headline = '',  # 标题
        self.msginfo = ''  # 正文

    # 生成header部分
    def funcSetHeader(self, Mykey):
        header = {}
        # time.time()的结果转成int有部分精度损失是被允许的
        timestamp = str(int(time.time()))
        # 生成一个1000-9999的随机数
        nonce = str(random.randint(1000, 9999))

        # 生成签名
        signature = tof4_sign(timestamp, Mykey.Token, nonce)
        # 在header中添加以下字段
        header['x-rio-paasid'] = Mykey.Paasid
        header['x-rio-nonce'] = nonce
        header['x-rio-timestamp'] = timestamp
        header['x-rio-signature'] = signature
        return header

    # 生成body部分
    def funcSetBody(self):
        # data完全复制到一个字典里传过去
        body = {
            "Sender": ','.join(self.sender),  # 发件人
            "Receiver": ','.join(self.receiver),  # 收件人
            "Title": ','.join(self.headline),  # 标题
            "MsgInfo": self.msginfo  # 内容
        }
        return json.dumps(body)

    # 发送
    def Send(self, URL, Mykey, Max_retries):
        headers = self.funcSetHeader(Mykey)
        body = self.funcSetBody()
        req1 = req.Session()
        retries = Retry(total=Max_retries,
                        backoff_factor=random.uniform(0, 0.1)
                        )
        req1.mount('http://', HTTPAdapter(max_retries=retries))
        req1.mount('https://', HTTPAdapter(max_retries=retries))
        try:
            response = req1.post(url=URL, headers=headers, data=body, timeout=5)
            # 打印返回码和错误码，不需要可以注释。
            print(response.content)
            print(response.status_code)
        except req.exceptions.RequestException as e:
            print(e)


# 订阅后可以看到的调用URL，可依据不同接入区域配置
# URL = 'http://127.0.0.1:18052/api/v1/Message/SendMail'

URL = 'http://rio.tencent.com/ebus/tof4_msg/api/v1/Message/SendRTXInfo'

# if __name__ == '__main__':
#     # 实例化一个Tof4RTX()对象为msg
#     msg = Tof4RTX()
#     msg.Title = 'TOF4_msg_SendRTXInfo_test'
#     msg.Content = "TOF4_msg_SendRTXInfo_test"
#     msg.From = 'disyli'
#     msg.To = 'disyli'
#
#     # 实例化一个Mykey()对象为key
#     key = MyKey()
#     key.Paasid = 'bglhbnhpihzfewxpexvhbg'
#     key.Token = 'r3RRvBI0Wmk7ScMjCItZUmpJ6Dhy60zd'
#
#     # send
#     max_retries = 3
#     msg.Send(URL=URL, Mykey=key, Max_retries=max_retries)
