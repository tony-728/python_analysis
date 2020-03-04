import datetime
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mpl_finance
import pandas as pd
import talib as ta
# 주봉데이터를 kiwoom AIP를 사용해서 가져오기 위해 임포트하는 모듈
from Kiwoom import *
import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time

class Quant:
    """
    # 로그: 2020.2.8시작, 2.18 수정
    # 기능: 주가 데이터에 볼리져밴드 값을 추가
    # 주요파라미터: code - 주가 코드, dtype - default(일봉), 주봉
    # 리턴: 볼린저 밴드가 추가된 주가 데이터프레임    """
    def add_bband(self, code, startdate, enddate=None, dtype='D', period=20, nbdevup=2, nbdevdn=2):
        if dtype =='W' and enddate is None:
            enddate = datetime.datetime.now().strftime("%Y-%m-%d")
            startdate = startdate.replace('-',"")
            enddate = enddate.replace('-',"")
            df = self.jubong_data(code, startdate, enddate).rename(columns=lambda col: col.lower())

        elif dtype == 'W' and enddate is not None:        
            startdate = startdate.replace('-',"")
            enddate = enddate.replace('-',"")
            df = self.jubong_data(code, startdate, enddate).rename(columns=lambda col: col.lower())

        if dtype == 'D':
            df = fdr.DataReader(code, startdate, enddate).rename(columns=lambda col: col.lower())

        ubb, mbb, lbb = ta.BBANDS(df['close'], period, nbdevup, nbdevdn)

        df['ubb'] = ubb
        df['mbb'] = mbb
        df['lbb'] = lbb

        return df
    '''
    로그: 2020.2.8시작, 2.14 수정
    기능: 키움API를 사용하여 HTS에서 주봉데이터를 가져옴
    리턴: 주봉 데이터프레임    '''
    def jubong_data(self, code, startdate, enddate):
        app = QApplication(sys.argv)
        kiwoom = Kiwoom()
        kiwoom.comm_connect()
        kiwoom.ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

        # opt10082 TR 요청
        kiwoom.set_input_value("종목코드", code)
        kiwoom.set_input_value("기준일자", enddate)
        kiwoom.set_input_value("수정주가구분", 1)
        kiwoom.comm_rq_data("opt10082_req", "opt10082", 0, "0101")

        while kiwoom.remained_data == True:

            time.sleep(TR_REQ_TIME_INTERVAL)
            kiwoom.set_input_value("종목코드", code)
            kiwoom.set_input_value("기준일자", enddate)
            kiwoom.set_input_value("수정주가구분", 1)
            kiwoom.comm_rq_data("opt10082_req", "opt10082", 2, "0101")

        # 키움에서 가져온 주봉데이터로 데이터 프레임을 만듬
        df = pd.DataFrame(kiwoom.ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=kiwoom.ohlcv['date'])
        df.reset_index(inplace=True)
        df = df[df['index'] >= startdate] # 시작 날짜로 슬라이싱
        
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']

        def y_m_d(x): # 날짜가 정수로 되어있으므로 y-m-d 형식에 맞춰 변경
            x = str(x)
            return datetime.datetime.strptime(x, '%Y%m%d').date()    
        df['Date'] = list(map(y_m_d, df['Date']))
        
        df.set_index('Date', inplace=True)
        df=df[::-1]

        return df
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

if __name__ == "__main__":  
    quant = Quant()  
    df = quant.add_bband(code='005930', startdate='2018-01-01', enddate='2019-01-01')

    candle = quant.check_candle(df=df)
    bbcross = quant.check_bbcross(df=df)
    rsi = quant.get_RSI(df=df)
    macd = quant.get_MACD(df=df)
    stoch = quant.get_stochastic(df=df)
   
    # result = quant.merge_all_df(df, candle, bbcross, rsi, macd, stoch)
    # print(result)
    # result.to_csv('2020-파이썬분석팀/quant_analysis/result_file/000660_result.csv')