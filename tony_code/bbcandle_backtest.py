import FinanceDataReader as fdr
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import zipline
# zipline을 이용해 알고리즘을 백테스트하려면 initialize, handle_data라는 이름의 함수를 구현해야한다.
from zipline.api import order_target, order, record, symbol, order_percent
# 백테스팅을 실행하기 위한 TradingAlgorithm 클래스를 임포트
from zipline.algorithm import TradingAlgorithm
from zipline.api import set_commission, commission # 수수료 설정에 사용되는 함수와 모듈
from trading_calendars import get_calendar # 해당 나라에 속하는 주식의 날짜를 맞추기 위해 필요한 모듈
import mpl_finance
import matplotlib.ticker as ticker
from pandas.tseries.offsets import Hour, Minute
import os # 파일이 있는지 확인하기 위해 사용하는 모듈

# context는 namespace로서 백테스트를 수행할 때 계속해서 유지해야 할 변수를 저장하는 용도로 사용한다.
def initialize(context):
    context.i = 0 # context라는 namespace에 i라는 변수는 거래일 수를 계산하는데 사용되는 변수이다. 
    
    # sym은 참조할 데이터에 대한 심볼을 저장하는데 사용된다.
    context.sym = symbol('close') 
    context.sym1 = symbol('high') # sell_check
    context.sym2 = symbol('low') # buy_check

    context.hold = False # 주식 보유 여부에 대한 정보를 저장하는 변수 hold 시뮬레이션 초기에는 주식을 가지고있지 않기 때문에 false
    set_commission(commission.PerDollar(cost=0.00165))

# 백테스트 시뮬레이션 동안 거래일마다 호출되는 함수인 handle_data 
# 함수의 인자로 context, data를 사용하는데 context는 TradingAlgorithm 클래스의 인스턴스이고 data는 BarData 클래스의 인스턴스이다.
def handle_data(context, data):
    context.i += 1
    # bband에서 20일 이평선을 사용하기 때문에 시뮬레이션 시작일로부터 최소 20일이 지난 후부터 계산할 수 있다. 
    # 따라서 context.i 값이 20보다 작을 때는 handle_data함수가 종료되도록 구현한다.
    if context.i <20: 
        return

    # 시뮬레이션 거래일 마다 매수 또는 매도 여부를 저장한 후 이를 record 함수를 사용해 시뮬레이션 결과에 추가
    buy = False
    sell = False

    sell_check = data.current(context.sym1, 'price')
    buy_check = data.current(context.sym2, 'price')

    # print('sell_check:', sell_check)
    # print('buy_check:', buy_check)

    if sell_check is True and context.hold == True:
        order_percent(context.sym, -0.96)
        context.hold = False
        sell = True
    elif buy_check is True and context.hold == False:
        order_percent(context.sym, 0.96)
        context.hold = True
        buy = True

    # 이평선값들을 저장하기 위해서 zipline에서는 record 함수를 제공한다.
    record(close=data.current(context.sym, "price"), buy = buy, sell = sell)

def handle_data_2(context, data):
    context.i += 1
    # bband에서 20일 이평선을 사용하기 때문에 시뮬레이션 시작일로부터 최소 20일이 지난 후부터 계산할 수 있다. 
    # 따라서 context.i 값이 20보다 작을 때는 handle_data함수가 종료되도록 구현한다.
    if context.i <20: 
        return

    # 시뮬레이션 거래일 마다 매수 또는 매도 여부를 저장한 후 이를 record 함수를 사용해 시뮬레이션 결과에 추가
    buy = False
    sell = False

    sell_check = data.current(context.sym1, 'price')
    buy_check = data.current(context.sym2, 'price')

    # if context.hold == True:
    #     order_percent(context.sym, -0.96)
    #     sell = True
    if buy_check is True and context.hold == False:
        order_percent(context.sym, 0.96)
        buy = True

    # 이평선값들을 저장하기 위해서 zipline에서는 record 함수를 제공한다.
    record(close=data.current(context.sym, "price"), buy = buy, sell = sell)

def set_calendar(cal):
    if cal == 'US':
        calendar = get_calendar('XNYS')
    elif cal == 'KR':
        calendar = get_calendar('XKRX')
    else:
        calendar = 'err'
    return calendar

'''
파라미터: zipline결과 데이터프레임, backtesting했던 주가데이터 프레임, 해당주식이 속한 나라
기능: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임을 그래프로 나타냄
'''
def make_graph(result, base_data, country = 'KR'):    
    '''기능: 그래프의 x축 format을 맞춰주기위한 함수'''    
    def x_date(x, pos):
        try:
            return index[int(x)][:10]
        except IndexError:
            return ''

    if country == 'KR':
        base_data = base_data.loc[result.index[0] - (6 * Hour() + 30 * Minute()): result.index[-1] + 7* Hour()]

    elif country == 'US':
    # backtesting 결과 인덱스와 캔들그래프로 그릴 data의 인덱스를 맞춰주기 위함 -> 그래야 x축이 같아져 함께 그릴 수 있다.
        base_data = base_data.loc[result.index[0] - (20 * Hour()): result.index[-1] + 7* Hour()]

    fig = plt.figure(figsize=(10,10))
    ax0 = fig.add_subplot(1,1,1)
    ax1 = ax0.twinx() # ax0과 x축을 공유하는 ax1 plot생성

    # 캔들 & 볼린져밴드, 매수매도 지점 그래프 생성
    # 그래프의 x축 format을 맞춰줌
    index = base_data.index.astype('str')
    ax0.xaxis.set_major_locator(ticker.MaxNLocator(12))
    ax0.xaxis.set_major_formatter(ticker.FuncFormatter(x_date))

    mpl_finance.candlestick2_ohlc(ax0, base_data['open'], base_data['high'], base_data['low'], base_data['close'], width=0.5, colorup='r', colordown='b')

    ax0.plot(index, base_data.ubb, label = 'Upper limit')
    ax0.plot(index, base_data.mbb, label = 'center line')
    ax0.plot(index, base_data.lbb, label = 'Lower limit')   
    ax0.plot(index[base_data.buy_check == True], base_data.lbb[base_data.buy_check == True], '^', label= 'buy') # 메수 지점에 ^표시
    ax0.plot(index[base_data.sell_check == True], base_data.ubb[base_data.sell_check == True], 'v', label= 'sell') # 매도 지점에 v표시    
    
    # 수익률 & 매수매도 지점 그래프 생성
    # 수익률 그래프의 x축을 datetime형식으로 맞춰주기 위해 변경함    
    result_index = result.index.astype('str')
    ax1.xaxis.set_major_locator(ticker.MaxNLocator(12))
    ax1.xaxis.set_major_formatter(ticker.FuncFormatter(x_date))         

    ax1.plot(result_index, result.portfolio_value, color='y')   
    ax1.plot(result_index[result.buy == True], result.portfolio_value[result.buy == True], '^', label= 'buy') # 메수 지점에 ^표시
    ax1.plot(result_index[result.sell == True], result.portfolio_value[result.sell == True], 'v', label= 'sell') # 매도 지점에 v표시

    #그래프의 범례와 기타 설정
    ax0.legend(loc='upper right')
    ax1.legend(loc='upper left')
    plt.xticks(rotation=45)

    plt.grid()
    plt.show()

if __name__ == "__main__":
    start = pd.to_datetime('2012-01-04').tz_localize('US/Eastern')
    end = pd.to_datetime('2019-12-30').tz_localize('US/Eastern')

    base_data = pd.read_csv('2020-파이썬분석팀/zipline/result_file/066570_result.csv')
    base_data['Date'] = pd.to_datetime(base_data['Date'])
    base_data.set_index('Date', inplace=True)

    base_data = base_data.tz_localize('UTC') # Datetime의 시간대를 설정함
    
    data = base_data[['close', 'sell_check', 'buy_check']]
    data.rename(columns={'sell_check':'high', 'buy_check': 'low'}, inplace=True)
    # print(data)

    result = zipline.run_algorithm(start=start,
                                    end=end,
                                    initialize=initialize,
                                    trading_calendar= set_calendar('KR'),
                                    capital_base=100000000,
                                    handle_data=handle_data_2,
                                    data=data)

    # result.to_csv('2020-파이썬분석팀/zipline/result_file/066570_week_backtest_result.csv') # zipline결과를 파일로 저장

    # print(result.info)
    # make_graph(result, base_data)
    print(result)

    fig = plt.figure(figsize=(10,10))
    ax0 = fig.add_subplot(1,1,1)

    ax0.plot(result.index, result.portfolio_value, color='y')   
    ax0.plot(result.index[result.buy == True], result.portfolio_value[result.buy == True], '^', label= 'buy') # 메수 지점에 ^표시
    
    plt.grid()
    plt.show()

