from quant import *
from strategy import *
if __name__ == "__main__":
    quant = Quant()
    df = quant.add_bband(code='000660', startdate='2010-01-01', enddate='2019-12-31')
    # df = quant.add_bband('000660','2010-01-01', dtype='W')
    rsi = quant.get_RSI(df=df)
    macd = quant.get_MACD(df=df)
    stoch = quant.get_stochastic(df=df)
   
    tech_df = quant.merge_all_df(df, rsi, macd, stoch)    
    # # print(tech_df)
    # tech_df.to_csv('C:/Users/ksang/Dropbox/파이썬 분석팀/quant/result/SK하이닉스/000660_tech_result(week).csv')

    # 기본전략 1 
    candle = quant.check_candle(df=df)
    bbcross = quant.check_bbcross(df=df)
    for_bbcandle = quant.merge_all_df(df, candle, bbcross)
    bbcandle = bbcandle_1(df=for_bbcandle)

    # sell_point_df_W, buy_point_df_W = bbcandle_1(df_W)

    # RSI
    rsi = check_RSI(df=rsi)
    # MACD
    macd = check_MACD(df=macd)    
    # stochastic
    stoch = check_STOCH(df=stoch)
    # print(stoch)
    df_for_trade = quant.merge_all_df(bbcandle, rsi, macd, stoch)   
    # print(df_for_trade)
    # df_for_trade['buy_point'] = (df_for_trade[:, 'bbcandle_buy']==True) & (df_for_trade[:, 'rsi_buy'] == True)



    # df_for_trade.to_csv('C:/Users/ksang/Dropbox/파이썬 분석팀/quant/result/코스피/KS11_trade_result(ver.2).csv')
    # df = quant.merge_for_backtest(df, sell_point_df_W, buy_point_df_W, dtype='W')

    result = make_trade_point(df=df_for_trade, tech_indicator=['rsi', 'stoch_2'])
    # result.to_csv('C:/Users/ksang/Dropbox/코스피/000660_macd_test(for_backtest).csv')
    # result = quant.merge_all_df(result, df, false='off')
    # print(result)

    # result = check_stop_loss(df=result)
    # print(result)
    # result.to_csv('C:/Users/ksang/Dropbox/코스피/for_backtest/KS11_for_backtest(ver.count-2+stoploss).csv')
    # quant.make_graph(result)