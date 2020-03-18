from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mpl_finance
import pandas as pd
import talib as ta
import time

class Quant:
    """
    # 로그: 2020.2.8시작, 2.18 수정
    # 기능: 주가 데이터에 볼리져밴드 값을 추가
    # 주요파라미터: code - 주가 코드, dtype - default(일봉), 주봉
    # 리턴: 볼린저 밴드가 추가된 주가 데이터프레임    """
    def add_bband(self, code, startdate, enddate=None, dtype='D', period=20, nbdevup=2, nbdevdn=2):
        if startdate == 'today' and dtype == 'D':
            startdate = datetime.now() + timedelta(days=-30)
            startdate = startdate.strftime('%Y-%m-%d')
            # print(startdate)
            # return

        elif startdate == 'today' and dtype == 'W':
            startdate = datetime.now() + relativedelta(months=-5)
            startdate = startdate.strftime('%Y-%m-%d')
            # print(startdate)
            # return

        if dtype =='W' and enddate is None:
            enddate = datetime.now().strftime("%Y-%m-%d")
            startdate = startdate.replace('-',"")
            enddate = enddate.replace('-',"")
            df = self.jubong_data(code, startdate, enddate).rename(columns=lambda col: col.lower())

        elif dtype == 'W' and enddate is not None:        
            startdate = startdate.replace('-',"")
            enddate = enddate.replace('-',"")
            df = self.jubong_data(code, startdate, enddate).rename(columns=lambda col: col.lower())

        if dtype == 'D':
            df = fdr.DataReader(code, startdate, enddate).rename(columns=lambda col: col.lower())

        # print(df)
        ubb, mbb, lbb = ta.BBANDS(df['close'], period, nbdevup, nbdevdn)

        df['ubb'] = ubb
        df['mbb'] = mbb
        df['lbb'] = lbb

        return df
    '''
    로그: 2020.2.8시작, 2020.03.18 수정
    기능: financedatereader에서 일봉데이터를 가져와서 주봉데이터에 맞게 변환
    리턴: 주봉 데이터프레임    '''
    def jubong_data(self, code, startdate, enddate):
        df = fdr.DataReader(code, startdate, enddate)
        # 주봉은 월요일을 기준으로 하므로 월요일기준으로 일 -> 주로 변환
        week_mon = df.resample('W-MON').last() 
        week_mon.reset_index(inplace=True)
        # 주봉데이터에 close는 금요일값을 기준으로 하므로 금요일기준으로 변환
        week_fri = df.resample('W-FRI').last()
        week_fri.reset_index(inplace=True)
        # 각각의 주의 최대값과 최소값을 찾음
        week_max = df.resample('W').max()
        week_max.reset_index(inplace=True)

        week_min = df.resample('W').min()
        week_min.reset_index(inplace=True)
        # 주봉데이터프레임 생성
        result = week_mon['Open'].to_frame()
        result['High'] = week_max['High'].to_frame()
        result['Low'] = week_min['Low'].to_frame()
        result['Close'] = week_fri['Close'].to_frame()
        result['Date'] = week_mon['Date'].to_frame()
        result.set_index('Date', inplace=True)
        # 현재가 있는 주는 open값을 제외한 값들은 계속 바뀌므로 금주를 기준으로 값을 채움
        result.iloc[-1, 1] = df.iloc[-1]['High']
        result.iloc[-1, 2] = df.iloc[-1]['Low']
        result.iloc[-1, 3] = df.iloc[-1]['Close']
        
        # 2017-09-29 ~ 2017-10-09 까지의 데이터가 없기 때문에 하드코딩으로 주봉데이터에 맞게 값을 맞춰줌
        # 2017-10-10 날짜에 주봉데이터를 생성함
        df.drop(df.index[df.index == '2017-10-02'], axis=0, inplace=True)
        df.loc['2017-10-09', 'Open'] = fdr.loc['2017-10-10', 'Open']
        df.reset_index(inplace=True)
        df['Date'] = pd.to_datetime(df['Date'])
        df.loc[404,'Date'] = datetime.strptime('2017-10-10', '%Y-%m-%d')
        df.set_index('Date',inplace=True)
        return result
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
    로그: 2020.02.16 시작 2020.02.24 수정
    파라미터: 일봉주가 데이터프레임, 주봉주가 데이터프레임으로 구한 매수, 매도 시그널데이터프레임
    기능: 주봉주가 데이터프레임으로 구한 매수, 매도 시그널을 백테스팅을 위해 일봉데이터프레임 인덱스로 변환
    리턴: 일봉주가데이터프레임에 주봉주가데이터로 구한 매수, 매도 시그널이 추가된 데이터프레임    '''
    def merge_for_backtest(self, df_D, sell_point_df, buy_point_df, dtype='D'):    
        if dtype == 'W': # 일봉 데이터 인덱스에 주봉 매수매도 신호 합치기
            sell_point_df['Date'] = pd.to_datetime(sell_point_df['Date'])
            buy_point_df['Date'] = pd.to_datetime(buy_point_df['Date'])
            
            df_D.reset_index(inplace=True)
            df_D = pd.merge(df_D, sell_point_df, how='outer')
            df_D = pd.merge(df_D, buy_point_df, how='outer')

        return df_D
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
    def check_stock(stockmarket, dtype='D'):
        stocklist = fdr.StockListing(stockmarket)
        code_data = {} # 각 주식코드의 시그널을 담기위한 dictionary
        if dtype == 'D':
            for no, stock in enumerate(stocklist.Symbol):
                df = quant.add_bband(code=stock, startdate='today')
                
                rsi = quant.get_RSI(df=df)
                macd = quant.get_MACD(df=df)
                stoch = quant.get_stochastic(df=df)  

                # 기본전략 시그널
                candle = quant.check_candle(df=df)
                bbcross = quant.check_bbcross(df=df)
                for_bbcandle = quant.merge_all_df(df, candle, bbcross)
                bbcandle = bbcandle_1(df=for_bbcandle)

                rsi = check_RSI(df=rsi)
                macd = check_MACD(df=macd)    
                stoch = check_STOCH(df=stoch)

                df_for_trade = quant.merge_all_df(bbcandle, rsi, macd, stoch)
                code_data[stock] = df_for_trade.iloc[-1]

        elif dtype == 'W': # 한번 조회밖에 안됨...
            for no, stock in enumerate(stocklist.Symbol):
                print(stock)
                df = quant.add_bband(code=stock, startdate='today', dtype='W')

                print(df)
                rsi = quant.get_RSI(df=df)
                macd = quant.get_MACD(df=df)
                stoch = quant.get_stochastic(df=df)  

                # 기본전략 시그널
                candle = quant.check_candle(df=df)
                bbcross = quant.check_bbcross(df=df)
                for_bbcandle = quant.merge_all_df(df, candle, bbcross)
                bbcandle = bbcandle_1(df=for_bbcandle)

                # 보조지표 시그널
                rsi = check_RSI(df=rsi)
                macd = check_MACD(df=macd)    
                stoch = check_STOCH(df=stoch)

                df_for_trade = quant.merge_all_df(bbcandle, rsi, macd, stoch)
                # print(df_for_trade)
                # print(stock, df_for_trade.iloc[-1])
                code_data[stock] = df_for_trade.iloc[-1]

                time.sleep(8) # 시간 텀을 두었지만 효과가 없었음...

        result = pd.DataFrame.from_dict(code_data)
        result = result.T
        result.index.names = ['stockcode']
        return result
        
if __name__ == "__main__":  
    quant = Quant()  
    # df = quant.add_bband(code='000660', startdate='today')
    df = quant.add_bband('041960',startdate='2010-01-01', dtype='W')
    df.to_csv('test_코미팜.csv')

    # df = quant.add_bband(code='005930', startdate='2018-01-01', enddate='2019-01-01')

    # candle = quant.check_candle(df=df)
    # bbcross = quant.check_bbcross(df=df)
    # rsi = quant.get_RSI(df=df)
    # macd = quant.get_MACD(df=df)
    # stoch = quant.get_stochastic(df=df)
   
    # result = quant.merge_all_df(df, candle, bbcross, rsi, macd, stoch)
    # print(result)
    # result.to_csv('2020-파이썬분석팀/quant_analysis/result_file/000660_result.csv')