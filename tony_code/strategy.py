from quant import *
'''
로그: 2020.2.8시작, 2.20 수정
기능: 기본전략(볼린져 밴드)을 이용하여 매수, 매도 타이밍 체크
리턴 매수, 매도 시점을 저장한 데이터프레임을 리턴
'''
def bbcandle_1(df, period=2): 
    quant = Quant()
    
    # 양봉 음봉 상향 하향 모두 일괄적으로 하기때문에 새롭게 값을 받아야한다.
    check_candle = quant.check_candle(df)
    check_bbcross = quant.check_bbcross(df)

    # df_sell = quant.check_candle(df) # 음봉인 캔들을 체크한 dataframe
    # df_up_cross = quant.check_bbcross(df) # 상향돌파를 체크한 dataframe

    sindex_list = check_candle[check_candle.down_candle == True].index # for문에 사용할 범위를 생성

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
                if check_bbcross.loc[i, 'up_cross']: # 상향돌파한 경우
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
    # df_buy = quant.check_candle(df, 'buy') # 양봉인 캔들을 체크한 dataframe
    # df_down_cross = quant.check_bbcross(df, 'buy') # 하향돌파를 체크한 dataframe

    bindex_list = check_candle[check_candle.up_candle == True].index # for문에 사용할 범위를 생성

    buy_point = {} # 매수 시점을 파악하기 위한 dict

    cross_signal = False # 돌파가 발생했을 때 체크하는 시그널
    candle_signal = False # 돌파이후 현재값이 첫번째 시그널 캔들인지 체크하는 시그널

    try: 
        for j in range(0, len(bindex_list)):
            if j - period < 0: # 처음 인덱스는 이전 데이터를 확인할 수 없으므로 넘어가도록 함
                continue

            for i in range(bindex_list[j] - period, bindex_list[j] + 1): # 정해진 기간내에서 하향돌파를 발생했는지 확인, 자신포함
                if check_bbcross.loc[i, 'down_cross']: # 하향돌파한 경우
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