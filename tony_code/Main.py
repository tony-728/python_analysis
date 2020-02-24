from quant import *
from strategy import *

if __name__ == "__main__":
    quant = Quant()

    df = quant.add_bband(code='KS11', startdate='2010-01-01', enddate='2019-01-01')
    # df_W = quant.add_bband('066570','2010-01-01', dtype='W')
    rsi = quant.get_RSI(df=df)
    macd = quant.get_MACD(df=df)
    stoch = quant.get_stochastic(df=df)
   
    tech_df = quant.merge_all_df(df, rsi, macd, stoch)    
    # print(tech_df)
    # tech_df.to_csv('2020-파이썬분석팀/zipline/result_file/KS11_tech_result.csv')

    # 기본전략 1 
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
    # df = quant.merge_for_backtest(df, sell_point_df_W, buy_point_df_W, dtype='W')

    result = make_trade_point(df=df_for_trade, tech_indicator='rsi')
    print(result)

    # df_for_trade.to_csv('2020-파이썬분석팀/zipline/result_file/KS11_trade_result.csv')
    # result = quant.merge_all_df(result, df)
    # quant.make_graph(result)