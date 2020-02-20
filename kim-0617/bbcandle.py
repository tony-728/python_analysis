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
# 로그: 2020.2.8시작, 2.14 수정
# 기능: 주가 데이터에 볼리져밴드 값을 추가
# 주요파라미터: code - 주가 코드, dtype - default(일봉), 주봉
# 리턴: 볼린저 밴드가 추가된 주가 데이터프레임
"""
def add_bband(code, startdate, enddate='today', dtype='D', period=20, nbdevup=2, nbdevdn=2):
    if enddate == 'today': # today를 바로 사용할 수 없으므로 실행한 날짜로 변경한다.
        enddate = datetime.datetime.now()    

    if dtype =='W':
        enddate=enddate.replace('-',"")
        startdate=startdate.replace('-',"")
        df=jubong_data(code,startdate,enddate).rename(columns=lambda col: col.lower())

    elif dtype == 'D':
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
def check_candle(df, type, up_pct=0, down_pct=0):
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

def make_Week_test(df_D,df_W):
    df=df_D.drop('sell_check',axis=1)
    df=df.drop('buy_check', axis=1)

    df2 = df_W[['Date', 'sell_check', 'buy_check']]
    a = pd.to_datetime(df['Date'])
    b = pd.to_datetime(df2['Date'])
    df['Date'] = a
    df2['Date'] = b
    d3 = pd.merge(df, df2, how='outer')
    return d3





if __name__ == "__main__":
    #df=add_bband('026890','2010-01-01','2019-12-30')
    df = add_bband('000660', '2010-01-01', '2019-12-30')
    df2=add_bband('000660','2010-01-01','2019-12-30','W')
    #print(df)
    #
    # # df = add_bband('US500', '2010-01-01')
    #
    sell_point_df, buy_point_df = bbcandle1_1(df)
    sell_point_df2, buy_point_df2 = bbcandle1_1(df2)
    #
    # # print(sell_point_df)
    #
    # # 위에서 만든 매수, 매도 시점의 dataframe의 인덱스가 정수 번호이므로 이에 맞춰 변경
    df.reset_index(inplace=True)
    df2.reset_index(inplace=True)
    #
    # # 총 3개의 dataframe을 병합
    df = pd.merge(df, sell_point_df, how='outer')
    df = pd.merge(df, buy_point_df, how='outer')
    #
    df2 = pd.merge(df2, sell_point_df2, how='outer')
    df2 = pd.merge(df2, buy_point_df2, how='outer')
    #
    # #df.to_csv('2020-파이썬분석팀/zipline/result_file/IXIC_result.csv', index=False)


    #df.to_csv('D.csv', index=False)
    #df2.to_csv('result2.csv', index=False)
    # # print(df)
    # # print("====================")
    # # print(df2)
    #
    #
    df3= make_Week_test(df,df2)
    # #print(type(df3['Date'][0]))
    #
    #df3.to_csv('W.csv', index=False)
    df['check']=df.sell_check==df3.sell_check
    print(df[df['check']==True])

    #make_graph(df)