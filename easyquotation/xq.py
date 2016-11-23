import requests
import json
import time


class Xueqiu:

    pankou_api = 'http://api.xueqiu.com/stock/pankou.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=E72E92&x=0.851&symbol=%s'
    detail_api = 'http://stock.xueqiu.com/stock/trade_detail.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479523207428&_S=92f079&x=0.8&count=10&symbol=%s'
    realtime_api = 'http://stock.xueqiu.com/stock/forchart/stocklist.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=92f075&one_min=1&symbol=%s&period=1d'
    kdata_api = 'http://stock.xueqiu.com/stock/forchartk/stocklist.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=92f075&begin=%s&end=%s&x=0.67&type=%s&symbol=%s&period=%s'
    general_api = 'http://stock.xueqiu.com/v4/stock/quote.json?_t=1huaweiBEB74FC21E3BAEB7EFD09915E42278E8.9558902513.1479522764315.1479522999943&_S=92f075&x=0.301&return_hasexist=1&isdelay=0&code=%s'

    def __init__(self):
        self.headers = {
            'Cookie': 'xq_a_token=xxxxxxxx;u=xxxxxxx,
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

    def get_pankou_data(self, code, retry_count=3, pause=0.001):
        """
        获取股票盘口数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
        return
        -------
            {"symbol":"SH601211","time":"Nov 23, 2016 2:59:58 PM","bp1":18.85,"bc1":447,"bp2":18.84,"bc2":248,"bp3":18.83,"bc3":1088,"bp4":18.82,"bc4":666,"bp5":18.81,"bc5":689,"bp6":0.0,"bc6":0,"bp7":0.0,"bc7":0,"bp8":0.0,"bc8":0,"bp9":0.0,"bc9":0,"bp10":0.0,"bc10":0,"current":18.85,"sp1":18.86,"sc1":969,"sp2":18.87,"sc2":92,"sp3":18.88,"sc3":287,"sp4":18.89,"sc4":582,"sp5":18.9,"sc5":1133,"sp6":0.0,"sc6":0,"sp7":0.0,"sc7":0,"sp8":0.0,"sc8":0,"sp9":0.0,"sc9":0,"sp10":0.0,"sc10":0,"buypct":50.6,"sellpct":49.4,"diff":75,"ratio":1.21}
        """
        symbol = self._code_to_symbol(code)
        url = self.pankou_api%(symbol)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url)
                stocks = json.loads(request.text)
                if len(stocks) == 0: #no data
                    print('no data')
                    return None
            except Exception as e:
                print(e)
            else:
                return stocks

    def get_detail_data(self, code, retry_count=3, pause=0.001):
        """
        获取股票分笔数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
        return
        -------
        {"list":
            [{"s":"SH601211","t":1479884398000,"ts":"14:59:58","c":18.85,"chg":-0.14,"pct":-0.74,"v":26400,"bp1":18.85,"sp1":18.86,"ttv":43696683,"type":-1,"avgPrice":18.99,"fileModifyTime":1479884406000},
            ...
        """
        symbol = self._code_to_symbol(code)
        url = self.detail_api % (symbol)
        for _ in range(retry_count):
            time.sleep(pause)
        try:
            request = self.session.get(url)
            stocks = json.loads(request.text)
            if len(stocks['list']) == 0:  # no data
                print('no data')
                return None
        except Exception as e:
            print(e)
        else:
            return stocks

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
            [{"s":"SH601211","t":1479884398000,"ts":"14:59:58","c":18.85,"chg":-0.14,"pct":-0.74,"v":26400,"bp1":18.85,"sp1":18.86,"ttv":43696683,"type":-1,"avgPrice":18.99,"fileModifyTime":1479884406000},
            ...
        """
        symbol = self._code_to_symbol(code)
        url = self.realtime_api % (symbol)
        for _ in range(retry_count):
            time.sleep(pause)
        try:
            request = self.session.get(url)
            stocks = json.loads(request.text)
            if len(stocks['chartlist']) == 0:  # no data
                print('no data')
                return None
        except Exception as e:
            print(e)
        else:
            return stocks

    def get_k_data(self, code, start='', end='', autype='normal', ktype='1day', retry_count=3, pause=0.001):
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
            {"chartlist":
            [{"volume":2068078,"open":23.65,"high":28.38,"close":28.38,"low":23.65,"chg":8.67,"percent":43.99,"turnrate":0.14,"ma5":28.38,"ma10":28.38,"ma20":28.38,"ma30":28.38,"dif":0.0,"dea":0.0,"macd":0.0,"time":"Fri Jun 26 00:00:00 +0800 2015"},
            ...
        """
        symbol = self._code_to_symbol(code)
        now = str(int(time.time() * 1000))
        if len(start) != 0:
            start_Array = time.strptime(start, "%Y-%m-%d %H:%M:%S")
            start = str(int(time.mktime(start_Array) * 1000))
        if len(end) != 0:
            end_Array = time.strptime(end, "%Y-%m-%d %H:%M:%S")
        end = str(int(time.mktime(end_Array) * 1000))
        url = self.realtime_api % (symbol)
        for _ in range(retry_count):
            time.sleep(pause)
        try:
            request = self.session.get(url)
            stocks = json.loads(request.text)
            if len(stocks['chartlist']) == 0:  # no data
                print('no data')
                return None
        except Exception as e:
            print(e)
        else:
            return stocks

    def get_general_data(self, code, retry_count=3, pause=0.001):
        """
        获取股票概要数据
        ---------
        Parameters:
            code:string
                      股票代码 e.g. 600848 或SH000001
        return
        -------
            {"SH601211":{"symbol":"SH601211","exchange":"SH","code":"601211","name":"国泰君安","current":"18.85",...
        """
        symbol = self._code_to_symbol(code)
        url = self.general_api%(symbol)
        for _ in range(retry_count):
            time.sleep(pause)
            try:
                request = self.session.get(url)
                stocks = json.loads(request.text)
                if len(stocks[symbol]) == 0: #no data
                    print('no data')
                    return None
            except Exception as e:
                print(e)
            else:
                return stocks

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
    q = Xueqiu()
    print(q.get_pankou_data('601211'))
    print(q.get_detail_data('601211'))
    print(q.get_realtime_data('601211'))
    print(q.get_k_data('601211', '2016-11-15 9:30:00', '2016-11-23 15:00:00'))
    print(q.get_general_data('601211'))
