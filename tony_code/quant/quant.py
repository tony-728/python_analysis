from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mpl_finance
import pandas as pd
import talib as ta
import time
from strategy import *

class Quant:
    """
    로그: 2020.2.8시작, 2.18 수정
    기능: 주가 데이터에 볼리져밴드 값을 추가
    주요파라미터: code - 주가 코드, dtype - default(일봉), 주봉
    리턴: 볼린저 밴드가 추가된 주가 데이터프레임    """
    def get_stock(self, code, startdate, enddate=None, dtype='D'):
        if startdate == 'today' and dtype == 'D':
            startdate = datetime.now() + timedelta(days=-30)
            startdate = startdate.strftime('%Y-%m-%d')
            # print(startdate)
            # return

        elif startdate == 'today' and dtype == 'W':
            startdate = datetime.now() + relativedelta(months=-5)
            startdate = startdate.strftime('%Y-%m-%d')

        if dtype == 'D':
            df = fdr.DataReader(code, startdate, enddate).rename(columns=lambda col: col.lower())

        elif dtype == 'W':
            df = self.jubong_data(code, startdate, enddate).rename(columns=lambda col: col.lower())

        return df
    '''
    로그: 2020.2.8시작, 2020.03.19 수정
    기능: financedatereader에서 일봉데이터를 가져와서 주봉데이터에 맞게 변환
    리턴: 주봉 데이터프레임    '''
    def jubong_data(self, code, startdate, enddate):
        fdr_df = fdr.DataReader(code, startdate, enddate)
        # resample를 위해 시작일을 월요일로 맞춰주기 위함
        day_index = fdr_df.index[0]; day = fdr_df.index[0].weekday() 
        if not day == 0: # 월요일이 아닌 날일 때
            if day == 1: # 화
                day_index = (day_index + timedelta(days=7-day))                
            elif day == 2: # 수
                day_index = (day_index + timedelta(days=7-day))                
            elif day == 3: # 목
                day_index = (day_index + timedelta(days=7-day))                
            elif day == 4: # 금
                day_index = (day_index + timedelta(days=7-day))                
            elif day == 5: # 토
                day_index = (day_index + timedelta(days=7-day))
            elif day == 6: # 일
                day_index = (day_index + timedelta(days=7-day))

        fdr_df = fdr_df[day_index:] # time series 시작을 월요일로 통일함
        # 주봉데이터프레임의 각 컬럼들을 구성하기 위해 필요한 데이터프레임 생성
        week_mon = fdr_df.resample('W-MON').last().reset_index()       
        week_fri = fdr_df.resample('W-FRI').last().reset_index()
        week_max = fdr_df.resample('W').max().reset_index()
        week_min = fdr_df.resample('W').min().reset_index()

        df = week_mon['Open'].to_frame()
        df['High'] = week_max['High'].to_frame()
        df['Low'] = week_min['Low'].to_frame()
        df['Close'] = week_fri['Close'].to_frame()
        df['Date'] = week_mon['Date'].to_frame()
        df.set_index('Date', inplace=True)

        # # 금주의 high, low, close 값은 달라지므로 변경해줌
        # df.iloc[-1, 1] = fdr_df.iloc[-1]['High']
        # df.iloc[-1, 2] = fdr_df.iloc[-1]['Low']
        # df.iloc[-1, 3] = fdr_df.iloc[-1]['Close']

        # startdate가 2017년 이전인지 아닌지 확인해야함 startdate가 2017-10-09이전이면 2017-10-09에 대한 처리를 해야함
        if datetime.strptime(startdate, '%Y-%m-%d').date() < datetime.strptime('2017-10-10', '%Y-%m-%d').date():
            df.drop(df.index[df.index == '2017-10-02'], axis=0, inplace=True)
            df.loc['2017-10-09', 'Open'] = fdr_df.loc['2017-10-10', 'Open']
            df.reset_index(inplace=True);  df['Date'] = pd.to_datetime(df['Date']) # 데이터프레임의 날짜형식을 변환하기 위함
            df.loc[df[df.Date == '2017-10-09'].index[0], 'Date'] = datetime.strptime('2017-10-10', '%Y-%m-%d') # 날짜를 변경 9일 -> 10일
            df.set_index('Date',inplace=True)

        # dateframe에 마지막 컬럼의resample하는 날짜가 금주를 넘어가기 때문에 삭제함
        df.drop(df.index[-1], inplace=True) 
        return df
    '''
    로그: 2020.3.19시작
    기능: 주가데이터로부터 볼린져밴드 값과 볼린져 밴드기반에 전략(기본전략)에 필요한 시그널을 구함
    파라미터: 주가데이터프레임, 이동평균기간, 표준편차의 상향값, 표준편차의 하향값, 캔들 상승비율, 캔들 하락비율
    리턴: 볼린져밴드 값+기본전략 시그널을 저장한 데이터프레임    '''
    def get_BBand(self, df, period=20, nbdevup=2, nbdevdn=2, up_pct=1.5, down_pct=0.5):
        # 볼린져 밴드 값 생성
        ubb, mbb, lbb = ta.BBANDS(df['close'], period, nbdevup, nbdevdn) 
        # bband_df = pd.DataFrame(data={'ubb':ubb, 'mbb':mbb, 'lbb':lbb})
        df['ubb'] = ubb; df['mbb'] = mbb; df['lbb'] = lbb

        check_candle = self.check_candle(df, up_pct=up_pct, down_pct=down_pct)
        check_bbcross = self.check_bbcross(df)

        bband_df = self.merge_all_df(df, check_candle, check_bbcross)

        return bband_df
    '''
    로그: 2020.2.8시작, 2.20 수정
    수정: type인자 삭제 - 매수 매도를 모두 구한후 이후 출력할 때 필터링하는 방식으로 변경
    기능: 주가데이터에서 어떤 캔들(양봉,음봉)인지 체크
    파라미터: 주가데이터프레임, 상승비율, 하락비율
    리턴: 해당 인덱스(date)가 음봉인지 양봉인지 체크한 데이터프레임    '''
    def check_candle(self, df, up_pct=1.5, down_pct=0.5):       
        down_candle = df['open'] * (1 - down_pct * 0.01) >= df['close'] # 시가기준 종가가 x% 하락한 음봉을 체크
        # df_sell = df_sell[df_sell.check == True] # 데이터프레임에 음봉인 경우만 남김
        up_candle = df['open'] * (1 + up_pct * 0.01) <= df['close'] # 시가기준 종가가 x% 상승한 양봉을 체크
        # df_buy = df_buy[df_buy.check == True] # 데이터프레임에 양봉 경우만 남김

        check_candle = pd.DataFrame({'up_candle':up_candle, 'down_candle':down_candle})

        return check_candle
    '''
    로그: 2020.2.8시작, 2.20 수정
    수정: type인자 삭제 - 매수 매도를 모두 구한후 이후 출력할 때 필터링하는 방식으로 변경
    기능: 주가데이터에서 어떤 돌파(상향, 하향)인지 체크
    파라미터: 주가데이터프레임
    리턴: 해당 인덱스(date)가 상향돌파인지 하향돌파인지 체크한 데이터프레임    '''
    def check_bbcross(self, df):
        up_cross = df['ubb'] <= df['high']
        # df_up_cross.reset_index(inplace=True)        
        down_cross = df['lbb'] >= df['low']
        # df_down_cross.reset_index(inplace=True)

        check_bbcross = pd.DataFrame({'up_cross':up_cross, 'down_cross':down_cross})
    
        return check_bbcross
    """
    로그: 2020.2.20 시작
    파라미터: 주가 데이터프레임, RSI를 확인할 기간
    기능: RSI 값을 가져오는 함수
    리턴: RSI 값을 저장한 데이터프레임    """
    def get_RSI(self, df, timeperiod=14):
        rsi = ta.RSI(df['close'], timeperiod) # series를 반환한다.
        rsi_df = pd.DataFrame(rsi, columns = ['rsi'])

        return rsi_df
    '''
    로그: 2020.2.20 시작
    파라미터: 주가 데이터프레임, 단기이평기간, 장기이평기간, 단기-장기 값의 이평의 이평기간
    기능: MACD 값을 가져오는 함수
    리턴: MACD 값을 저장한 데이터프레임    '''
    def get_MACD(self, df, fast_period=12, slow_period=26, signal_period=9):
        macd, macd_signal, macd_hist = ta.MACD(df['close'],fast_period, slow_period, signal_period)
        macd_df = pd.DataFrame({'macd':macd, 'macd_sig':macd_signal, 'macd_hist':macd_hist})

        return macd_df
    '''
    로그: 2020.2.20 시작
    파라미터: 주가 데이터프레임, 전체 기간(fastk_period,N), Fask %D, slow %K의 이평기간(slowk_period, M), slow %D의 이평기간(slowd_period, T)
    기능: stochastic 값을 가져오는 함수
    리턴: stochastic 값(slowk(fast %K를 M기간으로 이동평균), slowd(slow %K를 T기간으로 이동평균))을 저장한 데이터프레임    '''
    def get_stochastic(self, df, fastk_period=5, slowk_period=3, slowd_period=3):
        slowk, slowd = ta.STOCH(df['high'], df['low'], df['close'], fastk_period, slowk_period, slowd_period)
        stoch_df = pd.DataFrame({'slow_K':slowk, 'slow_D':slowd})

        return stoch_df    
    '''
    로그: 2020.2.16 시작
    파라미터: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임
    기능: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임을 그래프로 나타냄    '''
    def make_graph(self, df):       
        df.reset_index(inplace=True)
        ''' 기능: 그래프의 x축 format을 맞춰주기위한 함수 '''
        def x_date(x, pos):
            try:
                return index[int(x)][:10]
            except IndexError:
                return ''
                
        # 캔들 그래프의 x축을 datetime형식으로 맞춰주기 위해 변경함
        df.set_index('Date', inplace=True)
        index = df.index.astype('str')

        fig = plt.figure(figsize=(10,10))
        ax0 = fig.add_subplot(1,1,1)
        # ax1 = ax0.twinx() # x축이 같고 y축이 다른 그래프를 하나에 그래프에 그리기위한 메서드   

        # 캔들 그래프 생성
        ax0.xaxis.set_major_locator(ticker.MaxNLocator(12))
        ax0.xaxis.set_major_formatter(ticker.FuncFormatter(x_date))
        mpl_finance.candlestick2_ohlc(ax0, df['open'], df['high'], df['low'], df['close'], width=0.5, colorup='r', colordown='b')

        ax0.plot(index, df.ubb, label = 'Upper limit')
        ax0.plot(index, df.mbb, label = 'center line')
        ax0.plot(index, df.lbb, label = 'Lower limit')   
        ax0.plot(index[df.sell_point == True], df.ubb[df.sell_point == True], 'v', label= 'sell') # 매도 지점에 v표시
        ax0.plot(index[df.buy_point == True], df.lbb[df.buy_point == True], '^', label= 'buy') # 메수 지점에 ^표시
        
        ax0.legend(loc='best')
        plt.xticks(rotation=45)

        plt.grid()
        plt.show()
    '''
    로그: 2020.02.16 시작 2020.03.20 수정
    파라미터: 거래시그널 데이터프레임, 주가정보 데이터프레임, 시간 타입(일, 주)
    기능: 백테스팅과 캔들그래프를 함께 그리기 위해서 거래시그널과 주가정보를 하나의 데이터프레임으로 만들고 
        또한 주봉의 경우 time series를 일봉의 time series로 변환한다.
    리턴: 거래시그널과 주가정보가 통합된 데이터프레임    '''
    def backtest_for_week(self, code, startdate, enddate, signal_df):    
        # 일봉 데이터 인덱스에 주봉 매수매도 신호 합치기       
        fdr_df = fdr.DataReader(code, startdate, enddate).reset_index()
        signal_df.reset_index(inplace=True)

        result = pd.merge(fdr_df, signal_df, how='left').fillna(value=False).set_index('Date')

        return result
    '''
    로그: 2020.02.20 시작
    파라미터: 주가데이터와 모든 보조지표데이터프레임
    기능: 모든 보조지표들을 하나의 데이터프레임으로 합친다.
    리턴: 한 데이터프레임에 모든 주가데이터와 보조지표를 추가하여 리턴    '''
    def merge_all_df(self, *args, false='on'):
        result = pd.concat(args, axis='columns', join='outer')
        if false == 'on':            
            result.fillna(value=False, inplace=True)
        elif false == 'off':
            pass

        return result
    '''     
    로그: 2020.03.09 시작 2020.03.11 수정
    파라미터: 주식코드리스트, 가져올 기준시간(일봉 or 주봉)
    기능: 오늘기준으로 주식들의 시그널을 확인한다.
    리턴: 각각의 주식에대한 시그널    '''
    def check_stock(self, stockmarket, dtype='D'):
        stocklist = fdr.StockListing(stockmarket)
        code_data = {} # 각 주식코드의 시그널을 담기위한 dictionary
        if dtype == 'D':
            for no, stock in enumerate(stocklist.Symbol):
                df = self.get_stock(code=stock, startdate='today')
                
                bband = self.get_BBand(df=df)
                rsi = self.get_RSI(df=df)
                macd = self.get_MACD(df=df)
                stoch = self.get_stochastic(df=df)  

                # 기본전략 시그널
                bbcandle = check_bbcandle(df=bband)

                # 보조지표 시그널
                rsi = check_RSI(df=rsi)
                macd = check_MACD(df=macd)    
                stoch = check_STOCH(df=stoch)

                df_for_trade = self.merge_all_df(bbcandle, rsi, macd, stoch)
                code_data[stock] = df_for_trade.iloc[-1]

        elif dtype == 'W':
            for no, stock in enumerate(stocklist.Symbol):
                df = self.get_stock(code=stock, startdate='today', dtype='W')

                bband = self.get_BBand(df=df)
                rsi = self.get_RSI(df=df)
                macd = self.get_MACD(df=df)
                stoch = self.get_stochastic(df=df)  

                # 기본전략 시그널
                bbcandle = check_bbcandle(df=bband)
                # 보조지표 시그널
                rsi = check_RSI(df=rsi)
                macd = check_MACD(df=macd)    
                stoch = check_STOCH(df=stoch)

                df_for_trade = self.merge_all_df(bbcandle, rsi, macd, stoch)
                # print(df_for_trade)
                # print(stock, df_for_trade.iloc[-1])
                code_data[stock] = df_for_trade.iloc[-1]

        result = pd.DataFrame.from_dict(code_data)
        result = result.T
        result.index.names = ['stockcode']
        return result
    '''     
    로그: 2020.03.11 시작
    파라미터: 주식코드리스트, 전략, 기준시간(일봉 or 주봉)
    기능: 오늘기준으로 전략에 해당하는 주식 추출하기
    리턴: 데이터프레임에 실제 매수매도 시그널을 생성    '''
    def find_stock(self, stockmarket, strategy=None, dtype='D'):
        df = self.check_stock(stockmarket, dtype=dtype)
        result = make_trade_point(df, strategy)

        return result
        
if __name__ == "__main__":  
    quant = Quant()  
    df = quant.get_stock('000660', '2010-01-01', dtype='W')
    print(df.loc['2017-10-01':]) 

    # df = quant.check_stock(stockmarket='KOSPI', dtype='W')
    # print(df)
    
    # bband = quant.get_BBand(df=df)
    # print(bband)

    # df = quant.add_bband(code='005930', startdate='2018-01-01', enddate='2019-01-01')

    # candle = quant.check_candle(df=df)
    # bbcross = quant.check_bbcross(df=df)
    # rsi = quant.get_RSI(df=df)
    # macd = quant.get_MACD(df=df)
    # stoch = quant.get_stochastic(df=df)
   
    # result = quant.merge_all_df(df, candle, bbcross, rsi, macd, stoch)
    # print(result)
    # result.to_csv('2020-파이썬분석팀/quant_analysis/result_file/000660_result.csv')