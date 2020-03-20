from quant import *
from strategy import *

if __name__ == "__main__":
    quant = Quant()
    df = quant.get_stock(code='000660', startdate='2010-01-01', enddate='2019-12-31', dtype='W')
    bband = quant.get_BBand(df=df)
    rsi = quant.get_RSI(df=df)
    macd = quant.get_MACD(df=df)
    stoch = quant.get_stochastic(df=df)

    tech_df = quant.merge_all_df(df, rsi, macd, stoch)    
    # # print(tech_df)
    # tech_df.to_csv('C:/Users/ksang/Dropbox/파이썬 분석팀/quant/result/SK하이닉스/000660_tech_result(week).csv')

    # 기본전략
    bbcandle = check_bbcandle(df=bband)
    # RSI
    rsi = check_RSI(df=rsi)
    # MACD
    macd = check_MACD(df=macd)    
    # stochastic
    stoch = check_STOCH(df=stoch)
    # print(stoch)
    df_for_trade = quant.merge_all_df(bbcandle, rsi, macd, stoch)   
    # print(df_for_trade)

    # df_for_trade.to_csv('C:/Users/ksang/Dropbox/파이썬 분석팀/quant/result/코스피/KS11_trade_result(ver.2).csv')

    # 전략들의 조합으로 최종 거래 신호 발생
    trade_point_df = make_trade_point(df=df_for_trade)    
    print(trade_point_df)
    # 그래프와 백테스팅을 위해 데이터프레임 병합 - 일봉인 경우
    # result = quant.merge_all_df(trade_point_df, df)
    # print(result)

    # 그래프와 백테스팅을 위해 데이터프레임 병합 - 주봉인 경우
    result = quant.backtest_for_week('000660', startdate='2010-01-01', enddate='2019-12-31', signal_df=trade_point_df)
    print(result[result.buy_point == True])
    # print(result)

    # quant.make_graph(result) 