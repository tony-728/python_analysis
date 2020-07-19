from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import FinanceDataReader as fdr
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mpl_finance
import pandas as pd

class Gathering:
    """
    로그: 2020.2.8시작, 2.18 수정
    기능: 주가 데이터를 가져옴
    주요파라미터: code - 주가 코드, 시작날짜, 끝날짜, dtype - default(일봉), 주봉
    리턴: 볼린저 밴드가 추가된 주가 데이터프레임    """
    def get_stock(self, code, startdate, enddate=None, dtype='D'):
        # 처음 4개의 조건문은 check_stock에 대한 파라미터 처리이다.
        if startdate == 'today' and enddate == 'today':
            if dtype == 'D':
                startdate = datetime.now() + timedelta(days=-30)
                startdate = startdate.strftime('%Y-%m-%d')
                # print(startdate)
                # return

            elif dtype == 'W':
                startdate = datetime.now() + relativedelta(months=-5)
                startdate = startdate.strftime('%Y-%m-%d')
        elif startdate == enddate:
            if dtype == 'D':
                startdate = datetime.strptime(startdate, "%Y-%m-%d")
                startdate = startdate + timedelta(days=-30)
                startdate = startdate.strftime('%Y-%m-%d')

            elif dtype == 'W':
                startdate = datetime.strptime(startdate, "%Y-%m-%d")
                startdate = startdate + relativedelta(months=-5)
                startdate = startdate.strftime('%Y-%m-%d')

        if dtype == 'D':
            df = fdr.DataReader(code, startdate, enddate).rename(columns=lambda col: col.lower())

        elif dtype == 'W':
            df = self.get_week_stock(code, startdate, enddate).rename(columns=lambda col: col.lower())

        return df
    '''
    로그: 2020.2.8시작, 2020.03.19 수정
    기능: financedatereader에서 일봉데이터를 가져와서 주봉데이터에 맞게 변환
    리턴: 주봉 데이터프레임    '''
    def get_week_stock(self, code, startdate, enddate):
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
    로그: 2020.2.16 시작
    파라미터: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임
    기능: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임을 그래프로 나타냄    '''
    def make_graph(self, df, trade_point='on'):       
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

        if trade_point == 'on':
            ax0.plot(index, df.ubb, label = 'Upper limit')
            ax0.plot(index, df.mbb, label = 'center line')
            ax0.plot(index, df.lbb, label = 'Lower limit')   
            ax0.plot(index[df.sell_point == True], df.ubb[df.sell_point == True], 'v', label= 'sell') # 매도 지점에 v표시
            ax0.plot(index[df.buy_point == True], df.lbb[df.buy_point == True], '^', label= 'buy') # 메수 지점에 ^표시
        
        ''' 구현 중..
        elif trade_point == 'off':
            ax0.plot(index[df.sig == 'sell'], df.close[df.sig == 'sell'], 'v', label= 'sell') # 매도 지점에 v표시
            ax0.plot(index[df.sig == 'buy'], df.close[df.sig == 'buy'], '^', label= 'buy') # 메수 지점에 ^표시 '''
        
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
    def backtest_for_week(self, code, signal_df):    
        # 일봉 데이터 인덱스에 주봉 매수매도 신호 합치기
        startdate = signal_df.index[0].strftime('%Y-%m-%d')
        enddate = signal_df.index[-1].strftime('%Y-%m-%d') 
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