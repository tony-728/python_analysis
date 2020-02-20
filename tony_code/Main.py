from quant import *
from strategy import *

if __name__ == "__main__":
    quant = Quant()

    df = quant.add_bband(code='000660', startdate='2018-01-01', enddate='2019-01-01')    
    # df_W = quant.add_bband('066570','2010-01-01', dtype='W')
    

    sell_point_df, buy_point_df = bbcandle_1(df=df)
    # sell_point_df_W, buy_point_df_W = bbcandle_1(df_W)

    df = quant.merge_for_backtest(df, sell_point_df, buy_point_df)
    # df = quant.merge_for_backtest(df, sell_point_df_W, buy_point_df_W, dtype='W')
    # print(df)

    a = quant.check_stop_loss(df=df)
    print(a)
    # df.to_csv('2020-파이썬분석팀/zipline/result_file/KS11_result.csv', index=False)

    quant.make_graph(df)