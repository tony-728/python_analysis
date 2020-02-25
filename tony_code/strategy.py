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

# RSI 지표를 활용한 매수매도 check
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
로그: 2020.02.20 시작 2020.02.23 수정
파라미터: MACD 주가데이터프레임
기능: MACD 지표를 갖고 매수 매도 판단 시그널을 만든다.
리턴: 데이터프레임에 매수매도 판단 시그널을 생성    '''
def check_MACD(df):
    df.reset_index(inplace=True) # 인덱스 비교를 
    # MACD > 0 & MACD > MACD_sig -> buy
    # MACD가 0 초과인 인덱스를 찾고 그 인덱스에 있는 MACD가 MACD_sig를 골든크로스하는지 확인     
    macd_ovre_zero = df.macd > 0 # macd가 0보다 큰 인덱스에 True를 체크한 series
    macd_buy = {}
    for i in macd_ovre_zero[macd_ovre_zero.values == True].index: # True인 인덱스(macd>0)만 골든크로스를 하는지 비교
        if df.loc[i-1, 'macd_hist'] < 0 and df.loc[i, 'macd_hist'] > 0: # i 시점은 골든크로스가 발생, macd_hist = macd - macd_sig
            # 조건을 만족하는 i의 datetime을 True로 저장
            # print(df.loc[i, 'Date'])  # 조건이 맞는 datetime , 이제 이 날짜들로 데이터프레임을 만들어서 True로 값을 세팅하면 된다. 
            macd_buy[df.loc[i, 'Date']] = True # 매수 신호
    macd_buy_df = pd.DataFrame(macd_buy.items(), columns=['Date', 'macd_buy'])
    macd_buy_df.set_index('Date', inplace=True)
   
    # MACD < 0 & MACD < MACD_sig -> sell
    # MACD가 0 미만인 인덱스를 찾고 그 인덱스에 있는 MACD가 MACD_sig를 데드크로스하는지 확인
    macd_under_zero = df.macd < 0
    macd_sell = {}
    for i in macd_under_zero[macd_under_zero == True].index:
        if df.loc[i-1, 'macd_hist'] > 0 and df.loc[i, 'macd_hist'] < 0:
            # 조건을 만족하는 i의 datetime을 True로 저장
            macd_sell[df.loc[i, 'Date']] = True # 매도신호
    macd_sell_df = pd.DataFrame(macd_sell.items(), columns=['Date', 'macd_sell'])
    macd_sell_df.set_index('Date', inplace=True)

    result = pd.concat([macd_buy_df, macd_sell_df], axis='columns', join='outer')
    result.fillna(value=False, inplace=True)
    
    return result

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
        if df.loc[i+1, 'slow_K'] > down_pct:
            # print('20아래', df.loc[i, 'Date'], df.loc[i, 'slow_K'])
            # print('상향돌파', df.loc[i+1, 'Date'], df.loc[i+1, 'slow_K'])
            stoch_buy1[df.loc[i+1, 'Date']] = True # 매수신호
    stoch_buy1_df = pd.DataFrame(stoch_buy1.items(), columns=['Date', 'stoch_1_buy'])
    stoch_buy1_df.set_index('Date', inplace=True)

    stoch_over_up = df.slow_K >= up_pct
    stoch_sell1 = {}
    for i in stoch_over_up[stoch_over_up.values == True].index:
        if df.loc[i+1, 'slow_K'] < up_pct:
            # print('80이상', df.loc[i,'Date'], df.loc[i, 'slow_K'])
            # print('하향돌파', df.loc[i+1, 'Date'], df.loc[i+1, 'slow_K'])
            stoch_sell1[df.loc[i+1, 'Date']] = True # 매도신호
    stoch_sell1_df = pd.DataFrame(stoch_sell1.items(), columns=['Date', 'stoch_1_sell'])
    stoch_sell1_df.set_index('Date', inplace=True)

    '''case 2: 
        slow_K <= 20이고 slow_K가 slow_D를 상향돌파 하면 매수
        slow_K >= 80이고 slow_K가 slow_D를 하향돌파 하면서 매도 '''
    stoch_buy2 = {}
    for i in stoch_under_down[stoch_under_down.values == True].index:
        if df.loc[i+1, 'slow_K'] > df.loc[i+1, 'slow_D']:
            # print('20아래', df.loc[i, 'Date'], df.loc[i, 'slow_K'], df.loc[i, 'slow_D'])
            # print('상향돌파', df.loc[i+1, 'Date'], df.loc[i+1, 'slow_K'], df.loc[i+1, 'slow_D'])
            stoch_buy2[df.loc[i+1, 'Date']] = True
    stoch_buy2_df = pd.DataFrame(stoch_buy2.items(), columns=['Date', 'stoch_2_buy'])
    stoch_buy2_df.set_index('Date', inplace=True)

    stoch_sell2 = {}
    for i in stoch_over_up[stoch_over_up.values == True].index:
        if df.loc[i+1, 'slow_K'] < df.loc[i+1, 'slow_D']:
            # print('80이상', df.loc[i,'Date'], df.loc[i, 'slow_K'], df.loc[i, 'slow_D'])
            # print('하향돌파', df.loc[i+1, 'Date'], df.loc[i+1, 'slow_K'], df.loc[i+1, 'slow_D'])
            stoch_sell2[df.loc[i+1, 'Date']] = True
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
로그: 2020.02.24 시작
파라미터: 매수매도판단 시그널이 있는 데이터프레임, 어떤 보조지표를 사용할 것인지 또는 몇개의 보조지표를 사용할 것인지
기능: bbcandle과 보조지표의 신호를 확인하여 최종 거래 신호를 발생시킨다.
리턴: 데이터프레임에 실제 매수매도 시그널을 생성    '''
def make_trade_point(df, tech_indicator=None, indi_count=None):
    if tech_indicator: # 어떤 보조지표를 함께 확인할 것인지 정할 수 있다.
        result = df[['bbcandle_buy', 'bbcandle_sell']]
        for tech in tech_indicator: # 어떤 보조지표를 인자로 받아드렸는가에 따라 df 재생성
            if 'rsi' in tech_indicator:
                result[['rsi_buy','rsi_sell']] = df.loc[:,['rsi_buy','rsi_sell']]
            if 'macd' in tech_indicator:
                result[['macd_buy','macd_sell']] = df.loc[:,['macd_buy', 'macd_sell']]
            if 'stoch_1' in tech_indicator:
                result[['stoch_1_buy', 'stoch_1_sell']] = df.loc[:,['stoch_1_buy', 'stoch_1_sell']]
            if 'stoch_2' in tech_indicator:
                result[['stoch_2_buy', 'stoch_2_sell']] = df.loc[:,['stoch_2_buy', 'stoch_2_sell']]

        # print(result)
        # return
        # bbcandle과 보조지표가 동일한 지점에 거래포인트 생성
        buy_point = {}
        sell_point = {}
        # 매수신호: bbcandle과 rsi_buy가 함께 있는 지점
        bbcandle_buy_index = result[result.bbcandle_buy == True].index
        for i in bbcandle_buy_index: # bbcandle_buy가 True
            # print(i)
            for col in result.loc[i,:].index: # bbcandle_buy가 True인 행의 컬럼
                # print(i, col)
                if 'buy' in col and result.loc[i, col]: # col에 buy가 있고 그 컬럼이 True이면 거래신호
                    # print(i, col, result.loc[i, col], 'ok')
                    buy_point[i] = True
                elif 'buy' in col and not result.loc[i, col]:
                    # print(i, col, result.loc[i, col], 'nok')
                    buy_point[i] = False
                    break

        # 매도신호: bbcandle과 ris_sell이 함꼐 있는 지점
        bbcandle_sell_index = result[result.bbcandle_sell == True].index
        for i in bbcandle_sell_index:
            for col in result.loc[i,:].index:
                if 'sell' in col and result.loc[i, col]:
                    sell_point[i] = True
                elif 'sell' in col and not result.loc[i, col]:
                    sell_point[i] = False
                    break

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
        result = pd.concat([buy_point_df, sell_point_df], axis='columns', join='outer')

        return result
    except UnboundLocalError:
        print('indi_count는 1이상이여야 합니다.')
        return

    # 기본전략
    if not tech_indicator:
        result = df.drop(columns = ['rsi_buy', 'rsi_sell', 'macd_buy', 'macd_sell', 'stoch_1_buy', 
                            'stoch_1_sell', 'stoch_2_buy', 'stoch_2_sell'])
        result.rename(columns = {'bbcandle_sell':'sell_point', 'bbcandle_buy':'buy_point'}, inplace=True)
        
        return result