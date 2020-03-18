from quant import *
'''
로그: 2020.2.8시작, 2.24 수정
파라미터: 볼린져밴드와 보조지표가 모두 추가된 데이터프레임, 과거를 볼 기간
기능: 기본전략(볼린져 밴드)을 이용하여 매수, 매도 타이밍 체크
리턴 매수, 매도 시점을 저장한 데이터프레임을 리턴
'''
def bbcandle_1(df, period=2): 
    df.reset_index(inplace=True)
    # sell_check
    sindex_list = df[df.down_candle == True].index # for문에 사용할 범위를 생성

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
                if df.loc[i, 'up_cross']: # 상향돌파한 경우
                    cross_signal = True # 매도 신호 발생
                    cross_point = i  # 돌파한 시점의 인덱스      
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

                        if not candle_signal: # 한 번이라도 False가 나오면 매도신호에 맞지 않는다.
                            break
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
                # print(j, str(df_in_func['Date'].iloc[sindex_list[j]].strftime("%Y-%m-%d")) + ' SELL')
                sell_point[df_in_func['Date'].iloc[sindex_list[j]]] = True # 매도 시점을 저장
                cross_signal = False
                candle_signal = False
            # else:
                # print(str(df_in_func['Date'].iloc[sindex_list[j]].strftime("%Y-%m-%d")) + ' HOLD')
            # print('-----------------------------')
    except IndexError: # 데이터프레임에 존재하지 않는 인덱스를 확인할 때 발생하는 에러를 무시
        pass

    # check_buy
    bindex_list = df[df.up_candle == True].index # for문에 사용할 범위를 생성

    buy_point = {} # 매수 시점을 파악하기 위한 dict
    cross_signal = False # 돌파가 발생했을 때 체크하는 시그널
    candle_signal = False # 돌파이후 현재값이 첫번째 시그널 캔들인지 체크하는 시그널

    try: 
        for j in range(0, len(bindex_list)):
            if j - period < 0: # 처음 인덱스는 이전 데이터를 확인할 수 없으므로 넘어가도록 함
                continue

            for i in range(bindex_list[j] - period, bindex_list[j] + 1): # 정해진 기간내에서 하향돌파를 발생했는지 확인, 자신포함
                if df.loc[i, 'down_cross']: # 하향돌파한 경우
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

                        if not candle_signal: # 한 번이라도 False가 나오면 매수신호에 맞지 않는다.
                            break

                    else:
                        for k in range(cross_point, bindex_list[j]): # 돌파한 인덱스와 현재캔들 인덱스 사이에 양봉이 있는지 확인
                            if k in bindex_list: # 사이에 값이 양봉이 있는지 확인
                                candle_signal = False
                                break # print('사이에 양봉이 있습니다.')                                
                            else:
                                candle_signal = True
                                # print('사이에 양봉이 없습니다.')

                        if not candle_signal: # 한 번이라도 False가 나오면 매수신호에 맞지 않는다.
                            break
                    
            if cross_signal and candle_signal: # 돌파이후 현재 캔들이 첫번째 시그널캔들(양봉)인지를 확인
                # print(j, str(df_in_func['Date'].iloc[bindex_list[j]].strftime("%Y-%m-%d")) + " BUY")
                buy_point[df_in_func['Date'].iloc[bindex_list[j]]] = True
                cross_signal = False
                candle_signal = False
            # else:
            #     print(str(df_in_func['Date'].iloc[bindex_list[j]].strftime("%Y-%m-%d")) + " HOLD")
            # print('-----------------------------')
    except IndexError: # 데이터프레임에 존재하지 않는 인덱스를 확인할 때 발생하는 에러를 무시
        pass
    
    # 매수, 매도 시점을 저장한 딕셔너리를 dataframe으로 만듬
    bbcandle_buy = pd.DataFrame(buy_point.items(), columns=['Date', 'bbcandle_buy'])
    bbcandle_buy.set_index('Date', inplace=True)

    bbcandle_sell = pd.DataFrame(sell_point.items(), columns=['Date', 'bbcandle_sell'])
    bbcandle_sell.set_index('Date', inplace=True)

    result = pd.concat([bbcandle_buy, bbcandle_sell], axis='columns', join='outer')
    result.fillna(value=False, inplace=True)
    return result
'''
로그: 2020.02.20 시작
파라미터: RIS지표데이터프레임, RSI을 판단할 percentage
기능: RIS 지표를 갖고 매수 매도 판단 시그널을 만든다.
리턴: 데이터프레임에 매수매도 판단 시그널을 생성    '''
def check_RSI(df, up_pct=70, donw_pct=30):
    rsi_buy = df.rsi <= 30
    rsi_buy_df = pd.DataFrame({'rsi_buy':rsi_buy})

    rsi_sell = df.rsi >= 70
    rsi_sell_df = pd.DataFrame({'rsi_sell':rsi_sell})

    result = pd.concat([rsi_buy_df, rsi_sell_df], axis='columns')
    return result
'''
로그: 2020.02.20 시작 2020.03.03 수정
파라미터: MACD 주가데이터프레임
기능: MACD 지표를 갖고 하락세인지만 판단하도록 한다. (이유: 다른 지표들에서 더 좋은 거래 신호를 생성하기 때문에 )
리턴: 데이터프레임에 매수매도 판단 시그널을 생성    '''
def check_MACD(df):
    df.reset_index(inplace=True) # 인덱스 비교를 
    # macd < 0일땐 하락세인 것으로 예측하고 어떠한 거래를 하지 않도록 한다.
    macd_under_zero = df.macd< 0
    down_trend = {}
    for i in macd_under_zero[macd_under_zero == True].index: # macd<0인 날짜이므로 거래를 시키지 않는다.
        down_trend[df.loc[i,'Date']] = True
    down_trend_df = pd.DataFrame(down_trend.items(), columns=['Date', 'macd_DT'])
    down_trend_df.set_index('Date', inplace=True)

    return down_trend_df
'''
로그: 2020.02.20 시작 2020.02.24 수정
파라미터: stochastic 주가데이터와 stochastic 판단 percentage
기능: stochastic 지표를 갖고 매수 매도 판단 시그널을 만든다.
리턴: 데이터프레임에 매수매도 판단 시그널을 생성    '''
def check_STOCH(df, up_pct=80, down_pct=20):
    df.reset_index(inplace=True)
    '''case 1: 
        slow_K가 20 이하이면 과매도구간 slow_K가 20을 상향돌파하면 매수
        slow_K가 80 이상이면 과매수구간 slow_K가 80을 하향돌파하면 매도 '''
    stoch_under_down = df.slow_K <= down_pct
    stoch_buy1 = {}  
    for i in stoch_under_down[stoch_under_down.values == True].index:
        if df.loc[i-1, 'slow_K'] < down_pct and df.loc[i, 'slow_K'] > down_pct:
            # print('20아래', df.loc[i, 'Date'], df.loc[i, 'slow_K'])
            # print('상향돌파', df.loc[i+1, 'Date'], df.loc[i+1, 'slow_K'])
            stoch_buy1[df.loc[i, 'Date']] = True # 매수신호

    stoch_buy1_df = pd.DataFrame(stoch_buy1.items(), columns=['Date', 'stoch_1_buy'])
    stoch_buy1_df.set_index('Date', inplace=True)

    stoch_over_up = df.slow_K >= up_pct
    stoch_sell1 = {}
    for i in stoch_over_up[stoch_over_up.values == True].index:
        if df.loc[i-1, 'slow_K'] > up_pct and df.loc[i, 'slow_K'] < up_pct:
            # print('80이상', df.loc[i,'Date'], df.loc[i, 'slow_K'])
            # print('하향돌파', df.loc[i+1, 'Date'], df.loc[i+1, 'slow_K'])
            stoch_sell1[df.loc[i, 'Date']] = True # 매도신호
    stoch_sell1_df = pd.DataFrame(stoch_sell1.items(), columns=['Date', 'stoch_1_sell'])
    stoch_sell1_df.set_index('Date', inplace=True)

    '''case 2: 
        slow_K <= 20이고 slow_K가 slow_D를 상향돌파 하면 매수
        slow_K >= 80이고 slow_K가 slow_D를 하향돌파 하면서 매도 '''
    stoch_buy2 = {}
    for i in stoch_under_down[stoch_under_down.values == True].index:
        if df.loc[i-1, 'slow_K'] < df.loc[i-1, 'slow_D'] and df.loc[i, 'slow_K'] > df.loc[i, 'slow_D']:
            # print('20아래', df.loc[i-1, 'Date'], df.loc[i-1, 'slow_K'], df.loc[i-1, 'slow_D'])
            # print('상향돌파', df.loc[i, 'Date'], df.loc[i, 'slow_K'], df.loc[i, 'slow_D'])
            stoch_buy2[df.loc[i, 'Date']] = True

    stoch_buy2_df = pd.DataFrame(stoch_buy2.items(), columns=['Date', 'stoch_2_buy'])
    stoch_buy2_df.set_index('Date', inplace=True)

    stoch_sell2 = {}
    for i in stoch_over_up[stoch_over_up.values == True].index:
        if df.loc[i-1, 'slow_K'] > df.loc[i-1, 'slow_D'] and df.loc[i, 'slow_K'] < df.loc[i, 'slow_D']:
            # print('80이상', df.loc[i,'Date'], df.loc[i, 'slow_K'], df.loc[i, 'slow_D'])
            # print('하향돌파', df.loc[i+1, 'Date'], df.loc[i+1, 'slow_K'], df.loc[i+1, 'slow_D'])
            stoch_sell2[df.loc[i, 'Date']] = True
    stoch_sell2_df = pd.DataFrame(stoch_sell2.items(), columns=['Date', 'stoch_2_sell'])
    stoch_sell2_df.set_index('Date', inplace=True)

    result = pd.concat([stoch_buy1_df, stoch_sell1_df, stoch_buy2_df, stoch_sell2_df], axis='columns', join='outer')
    result.fillna(value=False, inplace=True)

    ''' case 1, 2의 결과가 좋지 않으면 case 3, 4번도 추가예정
    case 3: 
    df['close']는 저점을 갱신하면서 하락 slow_K는 전저점을 갱신하지 못한경우 -> 매수
    df['close']는 고점을 갱신하면서 상승 slow_K는 전고점을 갱신하지 못한경우 -> 매도
    case 4: 
    slow_K >= 50 and slow_D >= 50 -> 매수
    slow_K <= 50 and slow_D <= 50 -> 매도        '''
    return result
'''
로그: 2020.2.17 시작
수정: 리턴 값을 손절시점을 데이터프레임으로 한다.
파라미터: 매수 매도 포인트를 추가한 전체 데이터프레임, 손절 비율
기능: 매수와 매수 사이에 손절할 포인트가 있는지 확인하여 손절(매도)할 지점을 찾는다.    '''
def check_stop_loss(df, down_pct=5):
    df_func = df.reset_index()
    # 매수 신호의 인덱스, 매수와 매수 사이의 값들을 확인하면 된다.
    buy_index = df_func[df_func.loc[:,'buy_point'] == True].index 

    check_stop_loss = {} # stop_loss가 발생하는 시점을 저장하기 위한 딕셔너리

    for i in range(len(buy_index)): # 매수신호가 있는 만큼만 for loop을 돈다.
        try:
            for j in range(buy_index[i] + 1, buy_index[i + 1]): # 두 매수 신호 사이에(매도부분은 확인할 필요가 없다.) 손절할 부분이 있는지 확인해야함
                # 사이 구간에 매수한 가격(close)와 j의 인덱스가 가리키는 close가격을 비교하여 sell_check를 만들면된다. 
                # print(df.loc[buy_index[i], 'close'] * (1 - down_pct * 0.01))
                # return 
                if df_func.loc[buy_index[i], 'close'] * (1 - down_pct * 0.01) > df_func.loc[j, 'close']:
                    df.iloc[j, 1] = True
                    check_stop_loss[df_func.loc[j, 'Date']] = True
        except IndexError:
            pass

    print('check stop_loss done')

    check_stop_loss_df = pd.DataFrame(check_stop_loss.items(), columns=['Date', 'check_stop_loss'])
    check_stop_loss_df.set_index('Date', inplace=True)

    result = pd.concat([df, check_stop_loss_df], axis='columns', join='outer')
    return result
'''     
로그: 2020.02.24 시작 2020-03-12 수정
파라미터: 매수매도판단 시그널이 있는 데이터프레임, 어떤 보조지표를 사용할 것인지 또는 몇개의 보조지표를 사용할 것인지
기능: bbcandle과 보조지표의 신호를 확인하여 최종 거래 신호를 발생시킨다.
리턴: 데이터프레임에 실제 매수매도 시그널을 생성    '''
def make_trade_point(df, tech_indicator=None, indi_count=None):
    if tech_indicator: # 어떤 보조지표를 함께 확인할 것인지 정할 수 있다.
        result = tech_indicator_df(df, tech_indicator)        
        return result
    elif indi_count: # 몇 개에 보조지표를 확인할 것인지 정할 수 있다.
        buy_point = {}
        sell_point = {}
        # 매수신호: bbcandle과 함께 볼 보조지표를 확인후 생성
        bbcandle_buy_index = df[df.bbcandle_buy == True].index
        for i in bbcandle_buy_index:
            # print(i)
            true_count = 0
            for col in df.loc[i,:].index:
                # print(df.loc[i,:])
                if 'buy' in col and df.loc[i, col]:
                    true_count = true_count+1
                    # print(i, col, df.loc[i, col])
            
            if true_count-1 >= indi_count: # indi_count 이상의 보조지표를 확인한다.
                buy_point[i] = True       

        # 매도신호: bbcandle과 함께 볼 보조지표를 확인후 생성
        bbcandle_sell_index = df[df.bbcandle_sell == True].index
        for i in bbcandle_sell_index:
            true_count = 0
            for col in df.loc[i,:].index:
                if 'sell' in col and df.loc[i, col]:
                    true_count = true_count+1
            
            if true_count-1 >= indi_count:
                sell_point[i] = True

        try:
            buy_point_df = pd.DataFrame(buy_point.items(), columns=['Date', 'buy_point'])
            buy_point_df.set_index('Date', inplace=True)
            sell_point_df = pd.DataFrame(sell_point.items(), columns=['Date', 'sell_point'])
            sell_point_df.set_index('Date', inplace=True)
            result = pd.concat([buy_point_df, sell_point_df, df.loc[:, 'bbcandle_buy']], axis='columns', join='outer')
            result.fillna(value=False, inplace=True); result.drop(columns=['bbcandle_buy'], inplace=True)
            return result   
        except UnboundLocalError:
            pass

    if not tech_indicator:
        result = df.drop(columns = ['rsi_buy', 'rsi_sell', 'macd_DT', 'stoch_1_buy', 
                            'stoch_1_sell', 'stoch_2_buy', 'stoch_2_sell'])
        result.rename(columns = {'bbcandle_sell':'sell_point', 'bbcandle_buy':'buy_point'}, inplace=True)
        
        return result
'''     
로그: 2020-03-12 시작
파라미터: 매수매도판단 시그널이 있는 데이터프레임, 사용할 보조지표리스트
기능: bbcandle과 보조지표의 신호를 확인하여 최종 거래 신호를 발생시킨다.
리턴: 데이터프레임에 실제 매수매도 시그널을 생성    '''
def tech_indicator_df(df, tech_indicator):
    result = df[['bbcandle_buy', 'bbcandle_sell']]
    # 보조지표가 1개일 때
    if len(tech_indicator) == 1:
        if 'rsi' in tech_indicator:
            buy1 = 'rsi_buy'; sell1 = 'rsi_sell'
        elif 'macd' in tech_indicator:
            buy1 = 'macd_DT'; sell1 = 'macd_DT'
            result.loc[:,'buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:, buy1] == False)
            result.loc[:,'sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:, sell1] == False)

            result.drop(columns=['bbcandle_buy', 'bbcandle_sell'], inplace=True)
            # macd가 있으면 이 조건문안에서 처리한 후에 리턴해주어야한다. 
            return result

        elif 'stoch_1' in tech_indicator:
            buy1 = 'stoch_1_buy'; sell1 = 'stoch_1_sell'
        elif 'stoch_2' in tech_indicator:
            buy1 = 'stoch_2_buy'; sell1 = 'stoch_2_sell'
        
        result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:, buy1] == True)
        result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:, sell1] == True)
    
    # 보조지표가 2개일 떄
    elif len(tech_indicator) == 2:
        if 'rsi' in tech_indicator:
            buy1 = 'rsi_buy'; sell1 = 'rsi_sell'            
        if 'stoch_1' in tech_indicator:
            if not buy1:
                buy1 = 'stoch_1_buy'; sell1 = 'stoch_1_sell'
            else:
                buy2 = 'stoch_1_buy'; sell2 = 'stoch_1_sell'
        if 'stoch_2' in tech_indicator:
            if not buy1:
                buy1 = 'stoch_2_buy'; sell1 = 'stoch_2_sell'
            else:
                buy2 = 'stoch_2_buy'; sell2 = 'stoch_2_sell'
        if 'macd' in tech_indicator:
            buy2 = 'macd_DT'; sell2 = 'macd_DT'
            result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:,buy1] == True) & (df.loc[:,buy2] == False)
            result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:,sell1] == True) & (df.loc[:,sell2] == False)
            
            result.drop(columns=['bbcandle_buy', 'bbcandle_sell'], inplace=True)
            # macd가 있으면 이 조건문안에서 처리한 후에 리턴해주어야한다. 
            return result

        result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:,buy1] == True) & (df.loc[:,buy2] == True)
        result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:,sell1] == True) & (df.loc[:,sell2] == True)
    
    # 보조지표가 3개일 때
    elif len(tech_indicator) == 3:
        if 'rsi' in tech_indicator:
            buy1 = 'rsi_buy'; sell1 = 'rsi_sell'            
        if 'stoch_1' in tech_indicator:
            if not buy1:
                buy1 = 'stoch_1_buy'; sell1 = 'stoch_1_sell'
            else:
                buy2 = 'stoch_1_buy'; sell2 = 'stoch_1_sell'
        if 'stoch_2' in tech_indicator:
            if not buy1:
                buy1 = 'stoch_2_buy'; sell1 = 'stoch_2_sell'
            elif buy1 and not buy2:
                buy2 = 'stoch_2_buy'; sell2 = 'stoch_2_sell'
            elif buy1 and buy2:
                buy3 = 'stoch_2_buy'; sell3 = 'stoch_2_sell'
        if 'macd' in tech_indicator:
            buy3 = 'macd_DT'; sell3 = 'macd_DT'            
            result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:,buy1] == True) & (df.loc[:,buy2] == True) & (df.loc[:,buy3] == False)
            result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:,sell1] == True) & (df.loc[:,sell2] == True) & (df.loc[:,sell3] == False)
            
            result.drop(columns=['bbcandle_buy', 'bbcandle_sell'], inplace=True)
            # macd가 있으면 이 조건문안에서 처리한 후에 리턴해주어야한다. 
            return result

        result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:,buy1] == True) & (df.loc[:,buy2] == True) & (df.loc[:,buy3] == True)
        result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:,sell1] == True) & (df.loc[:,sell2] == True) & (df.loc[:,sell3] == True)
    
    # 보조지표가 4개일 때
    elif len(tech_indicator) == 4:
        result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:,'rsi_buy'] == True) & (df.loc[:,'stoch_1_buy'] == True) & (df.loc[:,'stoch_2_buy'] == True)  & (df['macd_DT'] == False)
        result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:,'rsi_sell'] == True) & (df.loc[:,'stoch_1_sell'] == True) & (df.loc[:,'stoch_2_sell'] == True)  & (df['macd_DT'] == False)
    
    result.drop(columns=['bbcandle_buy', 'bbcandle_sell'], inplace=True)
    return result
'''     
로그: 2020.03.11 시작
파라미터: 주식코드리스트, 전략, 기준시간(일봉 or 주봉)
기능: 오늘기준으로 전략에 해당하는 주식 추출하기
리턴: 데이터프레임에 실제 매수매도 시그널을 생성    '''
def find_stock(stockmarket, strategy=None, dtype='D'):
    df = check_stock(stockmarket, dtype=dtype)
    result = make_trade_point(df, strategy)

    return result

if __name__ == "__main__":
    # df = check_stock(stockmarket='KOSPI')
    # print(df)
    quant = Quant()

    df2 = find_stock(stockmarket='KOSPI', strategy=['rsi'])
    df2.to_csv('test.csv')