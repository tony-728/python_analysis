import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import datetime
import talib as ta


class SH_trader:
    def get_stockcode(self, market):        
        stockcode_df = fdr.StockListing(market)
        return stockcode_df.head(200)

    def get_stock_data(self, codes, startdate, enddate='today'):
        if enddate == 'today': # today를 바로 사용할 수 없으므로 실행한 날짜로 변경한다.
                enddate = datetime.datetime.now()
                
        code_df = self.get_stockcode("KOSDAQ")

        list_df =[] 
        if isinstance(codes, list):
            for code in codes:
                code_name = code_df[code_df.Symbol == code]
#                 print(code_name)
                
                day_price_df = fdr.DataReader(code, startdate, enddate).reset_index()
                
                day_price_df['code'] = code
                day_price_df['name'] = code_name.iloc[0,1]
                
                day_price_df = day_price_df.reindex(columns=['code','name','Date','Open','Close','High','Low','Volume','Change'])
                list_df.append(day_price_df)
        
        else:
            day_price_df = fdr.DataReader(codes, startdate, enddate)
            return day_price_df
        
        df = pd.concat(list_df, ignore_index=True)
        
        return df
    
    def get_ma(self, stockdata, mavol):
#         stockdata = stockdata.set_index('Date')
        stockdata.fillna(method='ffill') # 결측값을 이전 데이터로 채운다.
        ma = ta.MA(stockdata['Close'], timeperiod=mavol) # 
        return pd.DataFrame(ma , columns=['MA'])

    def check_arr(self, codes, startdate, enddate='today', filetype= 'txt'): # 정배열인지 확인하는 메서드
        
        if enddate == 'today': # today를 바로 사용할 수 없으므로 실행한 날짜로 변경한다.
                enddate = datetime.datetime.now()
        
        code_df = self.get_stockcode("KOSDAQ")

        if filetype== 'txt':
            f = open("2020-파이썬분석팀/kiwoom/sell_list.txt", 'w')
            
            for code in codes:
                code_name = code_df[code_df.Symbol == code]
                
                small_df = fdr.DataReader(code, startdate, enddate)
                
                short_ma = self.get_ma(small_df, 5)
                middle_ma = self.get_ma(small_df, 10)
                long_ma = self.get_ma(small_df, 20)   
            
                middle_ma['check'] = middle_ma['MA'] > long_ma['MA']
                middle_ma = middle_ma[middle_ma.check == True] # middle_ma에서 long_ma 보다 큰 값들만 남긴다.
                middle_ma = middle_ma.drop(['check'], axis=1)
                checked_index = [] # 추출한 인덱스를 넣기 위한 리스트

                # middle_ma에서 long_ma보다 큰 값들의 인덱스만을 short_ma에서 찾는다.
                for i in short_ma.index:
                    for j in middle_ma.index:
                        if i == j:
                            checked_index.append(i)

                short_ma = short_ma.reset_index()
                short_ma = short_ma[short_ma['Date'].isin(checked_index)] # short_ma에서 확인된 인덱스만 추출
                short_ma = short_ma.set_index(['Date'])

                short_ma['check'] = short_ma['MA'] > middle_ma['MA']
                short_ma = short_ma[short_ma.check == True]
                short_ma = short_ma.drop(['check'], axis=1)

                df = short_ma.tail(1).reset_index()
                # print(df)
                today = datetime.datetime.now()

                try:
                    if df.loc[0]['Date'].date() == today.date():
                        data = '매수;' +  code + ';'+ '시장가;' + '10;' + '0;' + '매수전\n'
                        f.write(data)
                except:
                    pass
            
            f.close()

        elif filetype == 'csv':
            code_list = [] # 정배열이 확인된 code를 넣는 리스트
            code_name_list = [] # 정배열이 확인된 code_name을 넣는 리스트

            for code in codes:
                code_name = code_df[code_df.Symbol == code]
                
                small_df = fdr.DataReader(code, startdate, enddate)
                
                short_ma = self.get_ma(small_df, 5)
                middle_ma = self.get_ma(small_df, 10)
                long_ma = self.get_ma(small_df, 20)   
            
                middle_ma['check'] = middle_ma['MA'] > long_ma['MA']
                middle_ma = middle_ma[middle_ma.check == True] # middle_ma에서 long_ma 보다 큰 값들만 남긴다.
                middle_ma = middle_ma.drop(['check'], axis=1)
                checked_index = [] # 추출한 인덱스를 넣기 위한 리스트

                # middle_ma에서 long_ma보다 큰 값들의 인덱스만을 short_ma에서 찾는다.
                for i in short_ma.index:
                    for j in middle_ma.index:
                        if i == j:
                            checked_index.append(i)

                short_ma = short_ma.reset_index()
                short_ma = short_ma[short_ma['Date'].isin(checked_index)] # short_ma에서 확인된 인덱스만 추출
                short_ma = short_ma.set_index(['Date'])

                short_ma['check'] = short_ma['MA'] > middle_ma['MA']
                short_ma = short_ma[short_ma.check == True]
                short_ma = short_ma.drop(['check'], axis=1)

                df = short_ma.tail(1).reset_index()
                # print(df)
                today = datetime.datetime.now()

                try:
                    if df.loc[0]['Date'].date() == today.date():
                        code_list.append(code)      
                        code_name_list.append(code_name.iloc[0,1])              
                except:
                    pass

            code_dict = {'code': code_list, 'name': code_name_list}
            df = pd.DataFrame(code_dict)
            df.to_csv('2020-파이썬분석팀/Kiwoom/checked_arr.csv', index=False)

        return 0

    def check_rarr(self, codes, startdate, enddate='today', filetype='txt'): # 역배열인지 확인하는 메서드
           
        if enddate == 'today': # today를 바로 사용할 수 없으므로 실행한 날짜로 변경한다.
                enddate = datetime.datetime.now()
        
        code_df = self.get_stockcode("KOSDAQ")

        if filetype == 'txt':
            f = open("2020-파이썬분석팀/Kiwoom/buy_list.txt", 'w')
            
            for code in codes:
                code_name = code_df[code_df.Symbol == code]
                
                small_df = fdr.DataReader(code, startdate, enddate)
                
                short_ma = self.get_ma(small_df, 5)
                middle_ma = self.get_ma(small_df, 10)
                long_ma = self.get_ma(small_df, 20)   
            
                middle_ma['check'] = middle_ma['MA'] > short_ma['MA']
                middle_ma = middle_ma[middle_ma.check == True] # middle_ma에서 long_ma 보다 큰 값들만 남긴다.
                middle_ma = middle_ma.drop(['check'], axis=1)
                checked_index = [] # 

                # middle_ma에서 long_ma보다 큰 값들의 인덱스만을 short_ma에서 찾는다.
                for i in long_ma.index:
                    for j in middle_ma.index:
                        if i == j:
                            checked_index.append(i)

                long_ma = long_ma.reset_index()
                long_ma = long_ma[long_ma['Date'].isin(checked_index)] # short_ma에서 확인된 인덱스만 추출
                long_ma = long_ma.set_index(['Date'])

                long_ma['check'] = long_ma['MA'] > middle_ma['MA']
                long_ma = long_ma[long_ma.check == True]
                long_ma = long_ma.drop(['check'], axis=1)

                df = long_ma.tail(1).reset_index()
                today = datetime.datetime.now()

                try:
                    if df.loc[0]['Date'].date() == today.date():
                        data = '매도;' +  code + ';'+ '시장가;' + '10;' + '0;' + '매도전\n'
                        # print(data)
                        f.write(data)
                except:
                    pass
            
            f.close()

        elif filetype == 'csv':
            code_list = [] # 역배열이 확인된 code를 넣는 리스트
            code_name_list = [] # 역배열이 확인된 code_name을 넣는 리스트

            for code in codes:
                code_name = code_df[code_df.Symbol == code]
                
                small_df = fdr.DataReader(code, startdate, enddate)
                
                short_ma = self.get_ma(small_df, 5)
                middle_ma = self.get_ma(small_df, 10)
                long_ma = self.get_ma(small_df, 20)   
            
                middle_ma['check'] = middle_ma['MA'] > short_ma['MA']
                middle_ma = middle_ma[middle_ma.check == True] # middle_ma에서 long_ma 보다 큰 값들만 남긴다.
                middle_ma = middle_ma.drop(['check'], axis=1)
                checked_index = [] # 

                # middle_ma에서 long_ma보다 큰 값들의 인덱스만을 short_ma에서 찾는다.
                for i in long_ma.index:
                    for j in middle_ma.index:
                        if i == j:
                            checked_index.append(i)

                long_ma = long_ma.reset_index()
                long_ma = long_ma[long_ma['Date'].isin(checked_index)] # short_ma에서 확인된 인덱스만 추출
                long_ma = long_ma.set_index(['Date'])

                long_ma['check'] = long_ma['MA'] > middle_ma['MA']
                long_ma = long_ma[long_ma.check == True]
                long_ma = long_ma.drop(['check'], axis=1)

                df = long_ma.tail(1).reset_index()
                today = datetime.datetime.now()

                try:
                    if df.loc[0]['Date'].date() == today.date():
                        code_list.append(code)      
                        # print(code_name.iloc[0,1])
                        code_name_list.append(code_name.iloc[0,1])              
                except:
                    pass
            
            code_dict = {'code': code_list, 'name': code_name_list}
            df = pd.DataFrame(code_dict)
            df.to_csv('2020-파이썬분석팀/Kiwoom/checked_rarr.csv', index=False)

        return 0

    def get_bbands(self, stockdata, timeperiod=5, nbdevup=2, nbdevdn=2):
        ubb, mbb, lbb = ta.BBANDS(stockdata['Close'], timeperiod, nbdevup, nbdevdn)
        return ubb, mbb, lbb


if __name__ == "__main__":
    sh = SH_trader()
    codes = sh.get_stockcode('KOSDAQ')
#     print(codes)

#     print(codes.Symbol)
    
    codes_list = list(codes.Symbol)
#     print(codes_list)
    
    # price_df = sh.get_stock_data(codes_list, startdate='2019-12-01')
#     print(price_df)

    price_df = sh.get_stock_data('200670', startdate='2019-12-01')
    # print(price_df)

#     ma5 = sh.get_ma(price_df, 5)
#     # print(ma5)

#     ma10 = sh.get_ma(price_df, 10)
#     # print(ma10)

#     ma20 = sh.get_ma(price_df, 20)
#     # print(ma20)

    # arr = sh.check_arr(codes_list, startdate='2019-12-01')
    # print(arr)
    
    # arr1, arr2, arr3 = sh.check_arr(codes_list, price_df)
    # print(arr1)
    # print(arr2)
    # print(arr3)

    rarr = sh.check_rarr(codes_list, startdate='2019-12-01', filetype='csv')
    print(rarr)

#     ubb, mbb, lbb = sh.get_bbands(price_df)
#     # print(ubb, mbb, lbb)