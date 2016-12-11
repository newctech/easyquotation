import requests
import sys
import time
import datetime
import asyncio
import json
import aiohttp
import easyutils
import yarl
import socket
from . import helpers



class Xueqiu:

    pankou_api = 'http://api.xueqiu.com/stock/pankou.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=E72E92&x=0.851&symbol=%s'
    detail_api = 'http://stock.xueqiu.com/stock/trade_detail.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479523207428&_S=92f079&x=0.8&count=10&symbol=%s'
    realtime_api = 'http://stock.xueqiu.com/stock/forchart/stocklist.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=92f075&one_min=1&symbol=%s&period=1d'
    kdata_api = 'http://stock.xueqiu.com/stock/forchartk/stocklist.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=92f075&begin=%s&end=%s&x=0.67&type=%s&period=%s&symbol=%s'
    general_api = 'http://stock.xueqiu.com/v4/stock/quote.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=92f075&x=0.301&return_hasexist=1&isdelay=0&code=%s'

    def __init__(self):
        self.headers = {
            'Cookie': 'xq_a_token=xxxxxxxx;u=xxxxxxx',
            'User-Agent': 'Xueqiu Android 8.8',
            'Host': 'stock.xueqiu.com',
            'Pragma': 'no-cache',
            'Connection': 'keep-alive',
            # 'Accept': '*/*',
            'Accept-Encoding': 'gzip',
            # 'Cache-Control': 'no-cache',
            # 'Referer': 'http://xueqiu.com/P/ZH003694',
            # 'X-Requested-With': 'XMLHttpRequest',
            'Accept-Language': 'zh-CN,zh;q=0.8'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.__pankoustocks = []
        self.__detailstocks = []
        self.__realtimestocks = []
        self.__kstocks = []
        self.__generalstocks = []

        self.all_market_api = self.gen_all_market_api()
        stock_codes = self.load_stock_codes()
        self.stock_list = self.gen_stock_list(stock_codes)

    def gen_all_market_api(self, start='midnight', ktype='60m'):
        if start == 'midnight':
            now = time.time()
            begin = str(int(now - (now % 86400) + time.timezone) * 1000)
        else:
            if len(start) != 0:
                start_Array = time.strptime(start, "%Y-%m-%d %H:%M:%S")
                begin = str(int(time.mktime(start_Array) * 1000))
            else:
                begin = ''
        api = self.kdata_api % (begin, '', 'normal', ktype, '')
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
    def all_market(self):
        """return quotation with stock_code prefix key"""
        return self.get_stock_data(self.stock_list)

    def stocks(self, stock_codes):
        if type(stock_codes) is not list:
            stock_codes = [stock_codes]

        stock_list = self.gen_stock_list(stock_codes)
        return self.get_stock_data(stock_list)

    async def get_stocks_by_range(self, params):
        url = yarl.URL(self.all_market_api + params, encoded=True)
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
        return '[' + ','.join([x for x in res if x is not None and len(x) > 2]) + ']'



    def get_pankou_data(self, code, retry_count=3, pause=0.001):
        """
        获取股票盘口数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
        return
        -------
            [{"symbol":"SH601211","time":"Nov 23, 2016 2:59:58 PM","bp1":18.85,"bc1":447,"bp2":18.84,"bc2":248,"bp3":18.83,"bc3":1088,"bp4":18.82,"bc4":666,"bp5":18.81,"bc5":689,"bp6":0.0,"bc6":0,"bp7":0.0,"bc7":0,"bp8":0.0,"bc8":0,"bp9":0.0,"bc9":0,"bp10":0.0,"bc10":0,"current":18.85,"sp1":18.86,"sc1":969,"sp2":18.87,"sc2":92,"sp3":18.88,"sc3":287,"sp4":18.89,"sc4":582,"sp5":18.9,"sc5":1133,"sp6":0.0,"sc6":0,"sp7":0.0,"sc7":0,"sp8":0.0,"sc8":0,"sp9":0.0,"sc9":0,"sp10":0.0,"sc10":0,"buypct":50.6,"sellpct":49.4,"diff":75,"ratio":1.21}]
        """
        stocks_list = []
        symbol = self._code_to_symbol(code)
        url = self.pankou_api%(symbol)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url)
                stock = json.loads(request.text)
                if len(stock) == 0: #no data
                    #print('no data')
                    return stocks_list
            except Exception as e:
                print(e)
            else:
                if stock in self.__pankoustocks:
                    pass
                else:
                    self.__pankoustocks.append(stock)
                    stocks_list.append(stock)
                    if len(self.__pankoustocks) > 5:
                        self.__pankoustocks.pop(0)
                return stocks_list

    def get_detail_data(self, code, retry_count=3, pause=0.001):
        """
        获取股票分笔数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
        return
        -------
            [{"s":"SH601211","t":1479884398000,"ts":"14:59:58","c":18.85,"chg":-0.14,"pct":-0.74,"v":26400,"bp1":18.85,"sp1":18.86,"ttv":43696683,"type":-1,"avgPrice":18.99,"fileModifyTime":1479884406000},
            ...
        """
        stocks_lists = []
        symbol = self._code_to_symbol(code)
        url = self.detail_api % (symbol)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url)
                stocks = json.loads(request.text)
                if len(stocks['list']) == 0:  # no data
                    #print('no data')
                    return stocks_lists
            except Exception as e:
                print(e)
            else:
                for stock in stocks['list']:
                    if stock in self.__detailstocks:
                        pass
                    else:
                        self.__detailstocks.append(stock)
                        stocks_lists.append(stock)
                        if len(self.__detailstocks) > 20:
                            self.__detailstocks.pop(0)
                return stocks_lists

    def get_realtime_data(self, code, retry_count=3, pause=0.001):
        """
        获取股票分时数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
        return
        -------
        {"list":
            [{"s":"SH601211","t":1479884398000,"ts":"14:59:58","c":18.85,"chg":-0.14,"pct":-0.74,"v":26400,"bp1":18.85,"sp1":18.86,"ttv":43696683,"type":-1,"avgPrice":18.99,"fileModifyTime":1479884406000}]
        """
        stocks_list = []
        symbol = self._code_to_symbol(code)
        url = self.realtime_api % (symbol)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url)
                stocks = json.loads(request.text)
                if len(stocks['chartlist']) == 0:  # no data
                    #print('no data')
                    return stocks_list
            except Exception as e:
                print(e)
            else:
                if stocks['chartlist'][-1] in self.__realtimestocks:
                    pass
                else:
                    self.__realtimestocks.append(stocks['chartlist'][-1])
                    stocks_list.append(stocks['chartlist'][-1])
                    if len(self.__realtimestocks) > 5:
                        self.__realtimestocks.pop(0)
                return stocks_list

    def get_kall_data(self, code, start='', end='', autype='normal', ktype='1day', retry_count=3, pause=0.001):
        """
        获取股票K线数据
        ---------
        Parameters:
          code:string
                      股票代码 e.g. 600848 或SH000001
          start:string
                      开始日期 format：YYYY-MM-DD HH:MM:SS为空时取当前日期
          end:string
                      结束日期 format：YYYY-MM-DD HH:MM:SS为空时取去年今日
          autype:string
                      复权类型，before-前复权 after-后复权 normal-不复权，默认为normal
          ktype：string
                      数据类型，1day=日k线 1week=周 1month=月 5m=5分钟 15m=15分钟 30m=30分钟，60m=60分钟，默认为1day
          retry_count : int, 默认 3
                     如遇网络等问题重复执行的次数
          pause : int, 默认 0
                    重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
        return
        -------
            [{"volume":2068078,"open":23.65,"high":28.38,"close":28.38,"low":23.65,"chg":8.67,"percent":43.99,"turnrate":0.14,"ma5":28.38,"ma10":28.38,"ma20":28.38,"ma30":28.38,"dif":0.0,"dea":0.0,"macd":0.0,"time":"Fri Jun 26 00:00:00 +0800 2015"},
            ...]
        """
        symbol = self._code_to_symbol(code)
        if len(start) != 0:
            start_Array = time.strptime(start, "%Y-%m-%d %H:%M:%S")
            start = str(int(time.mktime(start_Array) * 1000))
        if len(end) != 0:
            end_Array = time.strptime(end, "%Y-%m-%d %H:%M:%S")
            end = str(int(time.mktime(end_Array) * 1000))
        url = self.kdata_api % (start, end, autype, ktype, symbol)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url)
                stocks = json.loads(request.text)
                if len(stocks['chartlist']) == 0:  # no data
                    #print('no data')
                    return []
            except Exception as e:
                print(e)
            else:
                stocks_lists = stocks['chartlist']
                return stocks_lists

    def get_k_data(self, code, autype='normal', ktype='1day', retry_count=3, pause=0.001):
        """
        获取股票K线数据
        ---------
        Parameters:
          code:string
                      股票代码 e.g. 600848 或SH000001
          start:string
                      开始日期 format：YYYY-MM-DD HH:MM:SS为空时取当前日期
          end:string
                      结束日期 format：YYYY-MM-DD HH:MM:SS为空时取去年今日
          autype:string
                      复权类型，before-前复权 after-后复权 normal-不复权，默认为normal
          ktype：string
                      数据类型，1day=日k线 1week=周 1month=月 5m=5分钟 15m=15分钟 30m=30分钟，60m=60分钟，默认为1day
          retry_count : int, 默认 3
                     如遇网络等问题重复执行的次数
          pause : int, 默认 0
                    重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
        return
        -------
            [{"volume":2068078,"open":23.65,"high":28.38,"close":28.38,"low":23.65,"chg":8.67,"percent":43.99,"turnrate":0.14,"ma5":28.38,"ma10":28.38,"ma20":28.38,"ma30":28.38,"dif":0.0,"dea":0.0,"macd":0.0,"time":"Fri Jun 26 00:00:00 +0800 2015"},
            ...]
        """
        stocks_list = []
        yesterday = datetime.datetime.now() + datetime.timedelta(days=-1)
        yest_time = yesterday.strftime('%Y-%m-%d') + ' 15:00:00'
        today_time = time.strftime('%Y-%m-%d',time.localtime(time.time())) + ' 15:00:00'
        stock = self.get_kall_data(code, yest_time, today_time, autype, ktype, retry_count, pause)
        if stock is not None:
            if stock[-1] in self.__kstocks:
                pass
            else:
                self.__kstocks.append(stock[-1])
                stocks_list.append(stock[-1])
                if len(self.__kstocks) > 5:
                    self.__kstocks.pop(0)
        return stocks_list


    def get_general_data(self, code, retry_count=3, pause=0.001):
        """
        获取股票概要数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
        return
        -------
            [{"SH601211":{"symbol":"SH601211","exchange":"SH","code":"601211","name":"国泰君安","current":"18.85..}]
        """
        stocks_list = []
        symbol = self._code_to_symbol(code)
        url = self.general_api%(symbol)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url)
                stocks = json.loads(request.text)
                if len(stocks[symbol]) == 0: #no data
                    #print('no data')
                    return stocks_list
            except Exception as e:
                print(e)
            else:
                if stocks[symbol] in self.__generalstocks:
                    pass
                else:
                    self.__generalstocks.append(stocks[symbol])
                    stocks_list.append(stocks[symbol])
                    if len(self.__generalstocks) > 5:
                        self.__generalstocks.pop(0)
                return stocks_list

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
    clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_address = ('127.0.0.1', 8888)
    clientsocket.connect(server_address)
    q = Xueqiu()
    if len(sys.argv) == 2 and sys.argv[1] == 'init':
        #可获取一周内的数据,数据太多可能导致程序异常
        q.all_market_api = q.gen_all_market_api(start='2016-12-05 09:00:00')
    try:
        while True:
            data = q.all_market
            clientsocket.sendall(data.encode(encoding='utf_8') + 'EOF'.encode(encoding='utf_8'))
            #print(len(data))
            #time.sleep(10000000)
    except:
        pass
    finally:
        clientsocket.close()
    #print(q.get_pankou_data('601211'))
    #print(q.get_detail_data('601211'))
    #print(q.get_realtime_data('601211'))
    #print(q.get_k_data('601211'))
    #print(q.get_general_data('601211'))