# coding:utf-8
import requests
import time
import re
import json


class MySina:
    dadan_api = 'http://vip.stock.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_Bill.GetBillSum?symbol=%s&num=60&sort=ticktime&asc=0&volume=%s&amount=%s&type=0&day=%s'

    def __init__(self):
        self.headers = {
            'Accept-Encoding': 'gzip'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

        self.__dadanstocks = []



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
        stocks_list = []
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
                stock_res = json.loads(text)
                if stock_res is None or len(stock_res) == 0: #no data
                    #print('no data')
                    return stocks_list
            except Exception as e:
                print(e)
            else:
                stock = stock_res[-1]
                if stock in self.__dadanstocks:
                    pass
                else:
                    self.__dadanstocks.append(stock)
                    stocks_list.append(stock)
                    if len(self.__dadanstocks) > 5:
                        self.__dadanstocks.pop(0)
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
    q = MySina()

    print(q.get_dadan_data('601211', volume='50000', day='2016-12-30'))