# coding:utf-8
import requests
import time
import re
import json
import asyncio
import aiohttp
import easyutils
import yarl
import socket
from . import helpers


class MySina:
    dadan_api = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_Bill.GetBillSum?symbol=%s&num=60&sort=ticktime&asc=0&volume=%s&amount=%s&type=0&day=%s'
    dadan_detail_api = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_Bill.GetBillList?num=10000&page=1&sort=ticktime&asc=0&volume=%s&amount=%s&type=0&day=%s&symbol=%s'

    def __init__(self):
        self.headers = {
            'Accept-Encoding': 'gzip'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        self.__dadanstocks = []
        self.all_dadan_detail_api = self.gen_all_dadan_detail_api()
        stock_codes = self.load_stock_codes()
        self.stock_list = self.gen_stock_list(stock_codes)


    def gen_all_dadan_detail_api(self, volume='500000', amount='0', day=None):
        if day is None:
            day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        api = self.dadan_detail_api % (volume, amount, day, '')
        return api

    def gen_stock_list(self, stock_codes):
        stock_with_exchange_list = [easyutils.stock.get_stock_type(code) + code[-6:] for code in stock_codes]
        return stock_with_exchange_list

    @staticmethod
    def load_stock_codes():
        with open(helpers.stock_code_path()) as f:
            codes = json.load(f)['stock']
        stock_codes = []
        for index in range(len(codes)):
            if codes[index].startswith('000') or \
                    codes[index].startswith('002') or \
                    codes[index].startswith('600') or \
                    codes[index].startswith('601'):
                stock_codes.append(codes[index])
        return stock_codes

    @property
    def all_dadan_detail(self):
        """return quotation with stock_code prefix key"""
        return self.get_stock_data(self.stock_list)
    def dadan_detail_stocks(self, stock_codes):
        if type(stock_codes) is not list:
            stock_codes = [stock_codes]
        stock_list = self.gen_stock_list(stock_codes)
        return self.get_stock_data(stock_list)
    async def get_stocks_by_range(self, params):
        url = yarl.URL(self.all_dadan_detail_api + params, encoded=True)
        try:
            async with self.__session.get(url, timeout=10, headers=self.headers) as r:
                response_text = await r.text()
                return response_text
        except asyncio.TimeoutError:
            return None

    def get_stock_data(self, stock_list):
        self.__session = aiohttp.ClientSession()
        coroutines = []
        result_str = ''
        for params in stock_list:
            coroutine = self.get_stocks_by_range(params)
            coroutines.append(coroutine)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        res = loop.run_until_complete(asyncio.gather(*coroutines))
        self.__session.close()
        result =  '[' + ','.join([x for x in res if x is not None and len(x) > 4]) + ']'
        reg = re.compile(r'\,(\w*?)\:')
        text = reg.sub(r',"\1":', result)
        text = text.replace('"{symbol', '{"symbol')
        text = text.replace('{symbol', '{"symbol"')
        return text

    def get_dadan_data(self, code, volume='0', amount='0', day=None, retry_count=3, pause=0.001):
        """
        获取股票盘口数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
            volume:string
                      大单成交量(>=40000) e.g. 50000
            amount:string
                      大单成交量(>=500000) e.g. 500000
            day:string
                      日期 format：YYYY-MM-DD为空时取当前日期
        return
        -------
            [{symbol:"sh601211",name:"国泰君安",opendate:"2016-12-30",minvol:"0",voltype:"12",totalvol:"6409580",totalvolpct:"0.332",totalamt:"119029877",totalamtpct:"0.332",avgprice:"18.571",kuvolume:"4059125",kuamount:"75451044",kevolume:"0",keamount:"0",kdvolume:"2350455",kdamount:"43578832",stockvol:"19333129",stockamt:"358337978"}]
        """
        symbol = self._code_to_symbol(code)
        if day is None:
            day = time.strftime('%Y-%m-%d', time.localtime(time.time()))
        url = self.dadan_api%(symbol, volume, amount, day)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url).text
                reg = re.compile(r'\,(.*?)\:')
                text = reg.sub(r',"\1":', request)
                text = text.replace('"{symbol', '{"symbol')
                text = text.replace('{symbol', '{"symbol"')
                stock_list = json.loads(text)
                if stock_list is None or len(stock_list) == 0: #no data
                    #print('no data')
                    return []
            except Exception as e:
                print(e)
            else:
                if stock_list in self.__dadanstocks:
                    pass
                else:
                    self.__dadanstocks.append(stock_list)
                    if len(self.__dadanstocks) > 5:
                        self.__dadanstocks.pop(0)
                return stock_list

    def _code_to_symbol(self, code):
        """
            生成symbol代码标志
        """
        if len(code) == 8:
            return code
        elif len(code) == 6:
            return 'SH%s' % code if code[:1] in ['5', '6', '9'] else 'SZ%s' % code
        else:
            print('_code_to_symbol error: 请输入6位/8位股票')
            return ''


if __name__ == '__main__':
    q = MySina()
    q.all_dadan_detail_api = q.gen_all_dadan_detail_api(volume='2000000', day='2017-01-06')
    ret = q.all_dadan_detail
    stock_list = json.loads(ret)
    print(stock_list)

    #print(q.get_dadan_data('601211', volume='50000', day='2016-12-30'))