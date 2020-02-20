import FinanceDataReader as fdr
import pandas as pd
import talib as ta
import datetime
import matplotlib.pyplot as plt
import mpl_finance
import matplotlib.ticker as ticker

def answer(code,start,end,ws=21):
    df = fdr.DataReader(code, start, end)
    df = df.reset_index()
    df['sig'] = 'none'
    slist = df.index[(ws-1)//2:len(df) - (ws-1)//2]
    for i in slist:
        val_list = []
        for k in range(i - (ws - 1) // 2, i + (ws - 1) // 2):
           
            if (k > len(df)):
                break
            val_list.append(df.iloc[k]['Close'])

        max_val = max(val_list)
        min_val = min(val_list)

        if (df.iloc[i]['Close']  >= max_val * 0.95 and df.iloc[i]['Close']  <= max_val * 1.05):
            df.loc[i, 'sig'] = 'sell'
        elif (df.iloc[i]['Close'] >= min_val * 0.95 and df.iloc[i]['Close'] <= min_val * 1.05):
            df.loc[i, 'sig'] = 'buy'
        else:
            df.loc[i, 'sig'] = 'no sig'

    return df

def add_bband(code, startdate, enddate='today', dtype='D', period=20, nbdevup=2, nbdevdn=2):
    if enddate == 'today': # today를 바로 사용할 수 없으므로 실행한 날짜로 변경한다.
        enddate = datetime.datetime.now()

    # if dtype =='W':
    #     enddate=enddate.replace('-',"")
    #     startdate=startdate.replace('-',"")
    #     df=jubong_data(code,startdate,enddate).rename(columns=lambda col: col.lower())

    elif dtype == 'D':
        sig_df = answer(code, startdate, enddate)
        df =sig_df.rename(columns=lambda col: col.lower())


    ubb, mbb, lbb = ta.BBANDS(df['close'], period, nbdevup, nbdevdn)

    df['ubb'] = ubb
    df['mbb'] = mbb
    df['lbb'] = lbb

    return df



def make_graph(df):
    ''' 기능: 그래프의 x축 format을 맞춰주기위한 함수 '''

    def x_date(x, pos):
        try:
            return index[int(x)][:10]
        except IndexError:
            return ''

    # 캔들 그래프의 x축을 datetime형식으로 맞춰주기 위해 변경함
    df.set_index('date', inplace=True)
    index = df.index.astype('str')

    fig = plt.figure(figsize=(10, 10))
    ax0 = fig.add_subplot(1, 1, 1)
    # ax1 = ax0.twinx() # x축이 같고 y축이 다른 그래프를 하나에 그래프에 그리기위한 메서드

    # 캔들 그래프 생성
    ax0.xaxis.set_major_locator(ticker.MaxNLocator(12))
    ax0.xaxis.set_major_formatter(ticker.FuncFormatter(x_date))
    mpl_finance.candlestick2_ohlc(ax0, df['open'], df['high'], df['low'], df['close'], width=0.5, colorup='r',
                                  colordown='b')

    ax0.plot(index, df.ubb, label='Upper limit')
    ax0.plot(index, df.mbb, label='center line')
    ax0.plot(index, df.lbb, label='Lower limit')

    ax0.plot(index[df.sig == 'sell'], df.ubb[df.sig == 'sell'], 'v', label='sell')  # 매도 지점에 v표시
    ax0.plot(index[df.sig == 'buy'], df.lbb[df.sig == 'buy'], '^', label='buy')  # 메수 지점에 ^표시

    ax0.legend(loc='best')
    plt.xticks(rotation=45)

    plt.grid()
    plt.show()
# sig_df=answer('000660','2011-01-01','2012-01-01')
# print(sig_df)
sig_df=add_bband('026890','2011-01-01','2012-01-01')
make_graph(sig_df)
