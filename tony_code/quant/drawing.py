import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import mpl_finance

'''
로그: 2020.2.16 시작
파라미터: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임
기능: 볼린저 밴드 값과 거래 포인트가 추가된 데이터프레임을 그래프로 나타냄    '''
def make_graph(df, trade_point='on'):       
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