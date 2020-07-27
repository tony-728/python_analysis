import pandas as pd

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
        result = for_tech_indicator(df, tech_indicator)        
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
def for_tech_indicator(df, tech_indicator):
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

        elif 'stoch_2' in tech_indicator:
            buy1 = 'stoch_2_buy'; sell1 = 'stoch_2_sell'
        
        result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:, buy1] == True)
        result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:, sell1] == True)
    
    # 보조지표가 2개일 떄
    elif len(tech_indicator) == 2:
        if 'rsi' in tech_indicator:
            buy1 = 'rsi_buy'; sell1 = 'rsi_sell'            
        if 'stoch_2' in tech_indicator:
            if not buy1:
                buy1 = 'stoch2_buy'; sell1 = 'stoch2_sell'
            else:
                buy2 = 'stoch2_buy'; sell2 = 'stoch2_sell'
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
        if 'stoch_2' in tech_indicator:
            if not buy1:
                buy1 = 'stoch2_buy'; sell1 = 'stoch2_sell'
            elif buy1 and not buy2:
                buy2 = 'stoch2_buy'; sell2 = 'stoch2_sell'
            elif buy1 and buy2:
                buy3 = 'stoch2_buy'; sell3 = 'stoch2_sell'
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
        result['buy_point'] = (df.loc[:,'bbcandle_buy'] == True) & (df.loc[:,'rsi_buy'] == True) & (df.loc[:,'stoch2_buy'] == True)  & (df['macd_DT'] == False)
        result['sell_point'] = (df.loc[:,'bbcandle_sell'] == True) & (df.loc[:,'rsi_sell'] == True) & (df.loc[:,'stoch_1_sell'] == True) & (df.loc[:,'stoch2_sell'] == True)  & (df['macd_DT'] == False)
    
    result.drop(columns=['bbcandle_buy', 'bbcandle_sell'], inplace=True)
    return result   