from quant import *
from strategy import *

if __name__ == "__main__":
    quant = Quant()
    # 005930
    df = quant.add_bband(code='KS11', startdate='2010-01-01', enddate='2019-12-31')
    # df_W = quant.add_bband('005930','2010-01-01', dtype='W')
    rsi = quant.get_RSI(df=df)
    macd = quant.get_MACD(df=df)
    stoch = quant.get_stochastic(df=df)
   
    tech_df = quant.merge_all_df(df, rsi, macd, stoch)    
    # # print(tech_df)
    # tech_df.to_csv('2020-파이썬분석팀/zipline/result_file/000660_tech_result.csv')

    # # 기본전략 1 
    candle = quant.check_candle(df=df)
    bbcross = quant.check_bbcross(df=df)
    for_bbcandle = quant.merge_all_df(df, candle, bbcross)
    bbcandle = bbcandle_1(df=for_bbcandle)
    # print(bbcandle)
    # sell_point_df_W, buy_point_df_W = bbcandle_1(df_W)

    # RSI
    rsi = check_RSI(df=rsi)
    # MACD
    macd = check_MACD(df=macd)
    # stochastic
    stoch = check_STOCH(df=stoch)

    df_for_trade = quant.merge_all_df(bbcandle, rsi, macd, stoch)
    # df_for_trade.to_csv('2020-파이썬분석팀/zipline/result_file/000660_trade_result(test).csv')
    # print(df_for_trade)
    # df = quant.merge_for_backtest(df, sell_point_df_W, buy_point_df_W, dtype='W')

    # result = make_trade_point(df=df_for_trade, tech_indicator=['macd'])
    # print(result)
    # result.to_csv('2020-파이썬분석팀/zipline/result_file/SK하이닉스/000660_macd_test(for_backtest).csv')
    result = make_trade_point(df=df_for_trade, indi_count=2)
    result = quant.merge_all_df(result, df, false='off')
    # print(result)

    result = check_stop_loss(df=result)
    # print(result)
    result.to_csv('2020-파이썬분석팀/zipline/result_file/코스피/for_backtest/KS11_for_backtest(ver.count-2+stoploss).csv')
    quant.make_graph(result)