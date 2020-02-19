import FinanceDataReader as fdr
import pandas as pd
import talib as ta
import datetime
import matplotlib.pyplot as plt
import mpl_finance
import matplotlib.ticker as ticker

# 주봉데이터를 kiwoom AIP를 사용해서 가져오기 위해 임포트하는 모듈
from Kiwoom import *
import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time

"""
개발자: 
# 로그: 2020.2.8시작, 2.18 수정
# 기능: 주가 데이터에 볼리져밴드 값을 추가
# 주요파라미터: code - 주가 코드, dtype - default(일봉), 주봉
# 리턴: 볼린저 밴드가 추가된 주가 데이터프레임
"""
def add_bband(code, startdate, enddate=None, dtype='D', period=20, nbdevup=2, nbdevdn=2):
    if dtype =='W' and enddate is None:
        enddate = datetime.datetime.now().strftime("%Y-%m-%d")
        startdate=startdate.replace('-',"")
        enddate=enddate.replace('-',"")
        df=jubong_data(code,startdate,enddate).rename(columns=lambda col: col.lower())

    elif dtype == 'W' and enddate is not None:        
        startdate=startdate.replace('-',"")
        enddate=enddate.replace('-',"")
        df=jubong_data(code,startdate,enddate).rename(columns=lambda col: col.lower())

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
리턴: 주봉 데이터프레임
'''
def jubong_data(code,startdate,enddate):
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
로그: 2020.2.8시작, 2.12 수정
기능: 주가데이터에서 어떤 캔들(양봉,음봉)인지 체크
리턴: 해당 인덱스(date)가 음봉인지 양봉인지 체크한 데이터프레임
'''
def check_candle(df, type, up_pct=1.5, down_pct=0.5):
    if type == 'sell': # 매도인 경우
        df_sell = df['open'] * (1 - down_pct * 0.01) > df['close'] # 시가기준 종가가 x% 하락한 음봉을 체크
        df_sell = pd.DataFrame({'check': df_sell}) # seies를 dataframe으로 변경
        df_sell.reset_index(inplace=True) # 인덱스를 date 컬럼으로 변경
        df_sell = df_sell[df_sell.check == True] # 데이터프레임에 음봉인 경우만 남김

        return df_sell

    elif type == 'buy': # 매수인 경우
        df_buy = df['open'] * (1 + up_pct * 0.01) < df['close'] # 시가기준 종가가 x% 상승한 양봉을 체크
        df_buy = pd.DataFrame({'check': df_buy}) # series를 dataframe으로 변경
        df_buy.reset_index(inplace=True) # 인덱스를 date 컬럼으로 변경
        df_buy = df_buy[df_buy.check == True] # 데이터프레임에 양봉 경우만 남김

        return df_buy    

'''
로그: 2020.2.8시작, 2.12 수정
기능: 주가데이터에서 어떤 돌파(상향, 하향)인지 체크
리턴: 해당 인덱스(date)가 상향돌파인지 하향돌파인지 체크한 데이터프레임
'''
def check_bbcross(df, type):
    if type == 'sell': # upcross
        # 상향돌파 확인
        up_cross = df['ubb'] < df['high']
        df_up_cross = pd.DataFrame({'check': up_cross})
        df_up_cross.reset_index(inplace=True)

        return df_up_cross
    
    elif type == 'buy': # downcross
        # 하향돌파 확인
        down_cross = df['lbb'] > df['low']
        df_down_cross = pd.DataFrame({'check': down_cross})
        df_down_cross.reset_index(inplace=True)

        return df_down_cross

'''
로그: 2020.2.8시작, 2.12 수정
기능: 매수, 매도 타이밍 체크
리턴 매수, 매도 시점을 저장한 딕셔너리를 리턴
'''
def bbcandle1_1(df, period=2): 
    # check_sell
    df_sell = check_candle(df, 'sell') # 음봉인 캔들을 체크한 dataframe
    df_up_cross = check_bbcross(df, 'sell') # 상향돌파를 체크한 dataframe
    sindex_list = df_sell.index # for문에 사용할 범위를 생성

    sell_point = {} # 매도 시점을 파악하기 위한 dict

    df_in_func = df.reset_index() # 슬라이싱을 하기위해 date인덱스를 컬럼으로 변경

    cross_signal = False # 돌파가 발생했을 때 체크하는 시그널
    candle_signal = False # 돌파이후 현재값이 첫번째 시그널 캔들인지 체크하는 시그널
    try:
        for j in range(0, len(sindex_list)): # 음봉이 발생한 경우만 확인한다.
            # loop_count = 0 # period 루프가 돌아가는 횟수를 체크 
            if j - period < 0: # 처음 인덱스는 이전 데이터를 확인할 수 없으므로 넘어가도록 함
                continue

            for i in range(sindex_list[j] - period, sindex_list[j] + 1): # 정해진 기간내에서 상향돌파를 발생했는지 확인, 자신포함
                if df_up_cross.loc[i, 'check']: # 상향돌파한 경우
                    cross_signal = True # 매도 신호 발생
                    cross_point = i  # 돌파한 시점의 인덱스
                    # print('상향돌파한 인덱스', cross_point)                    

                    ''' 현재 시점 바로 이전에 돌파가 발생한 경우에 시그널을 주게 되면 첫번째 음봉체크가 불분명해진다. 때문에 현재도 확인을 해야함'''
                    # 자기 자신에서 상향돌파가 발생
                    if sindex_list[j] - cross_point == 0: # 현재시점 캔들(자기자신)에서 돌파가 발생 & 과거에 같은 경우(음봉이면서 상향돌파)가 있는지 확인해야한다.
                        for k in range(sindex_list[j] - period, cross_point): # sindex_list[j] == cross_point이므로 혼합하여 사용해도 된다.
                            # sell_point에 저장된 값이 있는지 확인하여 과거에 매도시점이 있는지 체크
                            if df_in_func['Date'].iloc[k] in sell_point:
                                candle_signal = False
                                break # 한 번이라도 False가 나오면 매도신호에 맞지 않는다.
                            else:
                                candle_signal = True

                        # if not candle_signal: # 한 번이라도 False가 나오면 매도신호에 맞지 않는다.
                        #     break

                    else: # 돌파한 인덱스와 현재캔들 인덱스 사이에 음봉이 있는지 확인 
                        for k in range(cross_point, sindex_list[j]): 
                            if k in sindex_list: # 사이에 음봉이 있는지 확인
                                candle_signal = False
                                break
                                # print('사이에 음봉이 있습니다.')
                            else:
                                candle_signal = True
                                # print('사이에 음봉이 없습니다.')

                        if not candle_signal: # 한 번이라도 False가 나오면(돌파시점과 현재시점사이에 한개에 음봉이라도 존재하는 경우) 매도신호에 맞지 않는다.
                            break
                
                # 음봉이면서 -> 하한돌파한경우 매수 신호로 체크한다. 

            if cross_signal and candle_signal:
                print(j, str(df_in_func['Date'].iloc[sindex_list[j]].strftime("%Y-%m-%d")) + ' SELL')
                sell_point[df_in_func['Date'].iloc[sindex_list[j]]] = True # 매도 시점을 저장
                cross_signal = False
                candle_signal = False
            # else:
                # print(str(df_in_func['Date'].iloc[sindex_list[j]].strftime("%Y-%m-%d")) + ' HOLD')
            # print('-----------------------------')
    except IndexError: # 데이터프레임에 존재하지 않는 인덱스를 확인할 때 발생하는 에러를 무시
        pass

    # check_buy
    df_buy = check_candle(df, 'buy') # 양봉인 캔들을 체크한 dataframe
    df_down_cross = check_bbcross(df, 'buy') # 하향돌파를 체크한 dataframe
    bindex_list = df_buy.index # for문에 사용할 범위를 생성

    buy_point = {} # 매수 시점을 파악하기 위한 dict

    cross_signal = False # 돌파가 발생했을 때 체크하는 시그널
    candle_signal = False # 돌파이후 현재값이 첫번째 시그널 캔들인지 체크하는 시그널

    try: 
        for j in range(0, len(bindex_list)):
            if j - period < 0: # 처음 인덱스는 이전 데이터를 확인할 수 없으므로 넘어가도록 함
                continue

            for i in range(bindex_list[j] - period, bindex_list[j] + 1): # 정해진 기간내에서 하향돌파를 발생했는지 확인, 자신포함
                if df_down_cross.loc[i, 'check']: # 하향돌파한 경우
                    cross_signal = True # 매수 신호 발생
                    cross_point = i # 돌파한 시점의 인덱스
                    
                    ''' 현재 시점 바로 이전에 돌파가 발생한 경우에 시그널을 주게 되면 첫번째 음봉체크가 불분명해진다.'''
                    if bindex_list[j] - cross_point == 0: # 현재시점 캔들에서 돌파가 발생하면 매도시그널 & 과거에도 같은 경우가 있는지 확인해야한다.
                        # buy_point에 저장된 값이 있는지 확인한다.
                        for k in range(bindex_list[j] - period, cross_point):# bindex_list[j] == cross_point이므로 혼합하여 사용해도 된다.
                            if df_in_func['Date'].iloc[k] in buy_point:
                                candle_signal = False
                                break
                            else:
                                candle_signal = True

                        if not candle_signal: # 한 번이라도 False가 나오면 매도신호에 맞지 않는다.
                            break

                    else:
                        for k in range(cross_point, bindex_list[j]): # 돌파한 인덱스와 현재캔들 인덱스 사이에 양봉이 있는지 확인
                            if k in bindex_list: # 사이에 값이 양봉이 있는지 확인
                                candle_signal = False
                                break
                                # print('사이에 양봉이 있습니다.')
                            else:
                                candle_signal = True
                                # print('사이에 양봉이 없습니다.')

                        if not candle_signal: # 한 번이라도 False가 나오면 매도신호에 맞지 않는다.
                            break
                       
            if cross_signal and candle_signal: # 돌파이후 현재 캔들이 첫번째 시그널캔들(양봉)인지를 확인
                print(j, str(df_in_func['Date'].iloc[bindex_list[j]].strftime("%Y-%m-%d")) + " BUY")
                buy_point[df_in_func['Date'].iloc[bindex_list[j]]] = True
                cross_signal = False
                candle_signal = False
            # else:
            #     print(str(df_in_func['Date'].iloc[bindex_list[j]].strftime("%Y-%m-%d")) + " HOLD")
            # print('-----------------------------')
    except IndexError: # 데이터프레임에 존재하지 않는 인덱스를 확인할 때 발생하는 에러를 무시
        pass
    
    # 매수, 매도 시점을 저장한 딕셔너리를 dataframe으로 만듬
    sell_point_df = pd.DataFrame(sell_point, index=[0])
    buy_point_df = pd.DataFrame(buy_point, index=[0])

    # print(sell_point)
    sell_point_df = sell_point_df.stack().reset_index().drop(['level_0'], axis='columns')
    buy_point_df = buy_point_df.stack().reset_index().drop(['level_0'], axis='columns')

    sell_point_df.rename(columns = {'level_1': 'Date', 0: 'sell_check'}, inplace= True)
    buy_point_df.rename(columns = {'level_1': 'Date', 0: 'buy_check'}, inplace= True)

    return sell_point_df, buy_point_df # 매수, 매도 시점을 저장한 데이터프레임을 반환
    
'''
파라미터: 매수 매도 포인트를 추가한 전체 데이터프레임
기능: 매수와 매수 사이에 손절할 포인트가 있는지 확인하여 sell_check에 추가
'''
def check_stop_loss(df, down_pct=5):
    ''' 매수와 매수 사이의 값들을 확인하면 된다. 때문에 매수인부분만 for loop을 돌면서 현재 매수와 다음 매수 사이에 손절할 부분이 있는지 확인하면 된다. '''
    # 매수 신호의 인덱스
    buy_index = df[df['buy_check'] == True].index 

    for i in range(len(buy_index)): # 매수신호가 있는 만큼만 for loop을 돈다.
        try:
            for j in range(buy_index[i] + 1, buy_index[i + 1]): # 두 매수 신호 사이에(매도부분은 확인할 필요가 없다.) 손절할 부분이 있는지 확인해야함
                # 사이 구간에 매수한 가격(close)와 j의 인덱스가 가리키는 close가격을 비교하여 sell_check를 만들면된다. 
                # print(df.loc[buy_index[i], 'close'] * (1 - down_pct * 0.01))
                # return 
                if df.loc[buy_index[i], 'close'] * (1 - down_pct * 0.01) > df.loc[j, 'close']:
                    df.loc[j, 'sell_check'] = True
        except IndexError:
            pass

    print('check stop_loss done')
    return

'''
파라미터: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임
기능: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임을 그래프로 나타냄
'''
def make_graph(df):       
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
    ax0.plot(index[df.sell_check == True], df.ubb[df.sell_check == True], 'v', label= 'sell') # 매도 지점에 v표시
    ax0.plot(index[df.buy_check == True], df.lbb[df.buy_check == True], '^', label= 'buy') # 메수 지점에 ^표시
    
    ax0.legend(loc='best')
    plt.xticks(rotation=45)

    plt.grid()
    plt.show()

'''
파라미터: 일봉주가 데이터프레임, 주봉주가 데이터프레임으로 구한 매수, 매도 시그널데이터프레임
기능: 주봉주가 데이터프레임으로 구한 매수, 매도 시그널을 백테스팅을 위해 일봉데이터프레임 인덱스로 변환
리턴: 일봉주가데이터프레임에 주봉주가데이터로 구한 매수, 매도 시그널이 추가된 데이터프레임
'''
def merge_df(df_D, sell_point_df, buy_point_df, dtype='D'):    
    if dtype == 'D': # 일봉 데이터끼리 합치기
        sell_buy_point_df = pd.merge(sell_point_df, buy_point_df, how='outer')
        df_D.reset_index(inplace=True)
        df_D = pd.merge(df_D, sell_buy_point_df, how='outer')

    elif dtype == 'W': # 일봉 데이터 인덱스에 주봉 매수매도 신호 합치기
        sell_point_df['Date'] = pd.to_datetime(sell_point_df['Date'])
        buy_point_df['Date'] = pd.to_datetime(buy_point_df['Date'])
        
        df_D.reset_index(inplace=True)
        df_D = pd.merge(df_D, sell_point_df, how='outer')
        df_D = pd.merge(df_D, buy_point_df, how='outer')

    return df_D

if __name__ == "__main__":
    df = add_bband('066570','2010-01-01')    
    df_W = add_bband('066570','2010-01-01', dtype='W')
    

    # sell_point_df, buy_point_df = bbcandle1_1(df)
    sell_point_df_W, buy_point_df_W = bbcandle1_1(df_W)

    df = merge_df(df, sell_point_df_W, buy_point_df_W, dtype='W')
    # df = merge_df(df, sell_point_df, buy_point_df)
    # print(df)

 

    # check_stop_loss(df)
    df.to_csv('2020-파이썬분석팀/zipline/result_file/066570_week_result.csv', index=False)

    make_graph(df)