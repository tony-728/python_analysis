#%%
from Gathering import *
from Tech_Indi import *
from Signal import *
from Strategy import *

if __name__ == "__main__":
    gathering = Gathering()
    techIndi = TechIndi()
    signal = Signal()
    strategy = Strategy()

    # 주가 정보 얻어오기
    df = gathering.get_stock(code='000660', startdate='2010-01-01', enddate='2019-12-30', dtype='D')
    print(df)
#%%
    # 기술적지표 생성, 볼린져 밴드 값
    bband_df = techIndi.get_BBand(df=df, period=20, nbdevup=2, nbdevdn=2, up_pct=1.5, down_pct=0.5)
    print(bband_df)
#%%
    # 기술적지표 생성, RSI 값
    rsi_df = techIndi.get_RSI(df, timeperiod=14)
    print(rsi_df)
#%%
    # 기술적지표 생성, macd 값
    macd_df = techIndi.get_MACD(df, fast_period=12, slow_period=26, signal_period=9)
    print(macd_df)
#%%
    # 기술적지표 생성, stochastic 값
    stoch_df = techIndi.get_STOCH(df, fastk_period=5, slowk_period=3, slowd_period=3)
    print(stoch_df)
#%%
    # 위에서 생성한 기술적 지표를 하나의 df로 병합
    techindi_df = gathering.merge_all_df(bband_df, rsi_df, macd_df, stoch_df)
    print(techindi_df)
#%%
    # 조건에 맞는 지표를 거래 신호를 생성, 볼린져 밴드값을 이용하여 거래 신호 생성
    check_bband = signal.check_bbcandle(bband_df, period=2) # 현재포함 과거 2일을 확인
    print(check_bband)
#%%
    # rsi값을 이용하여 거래신호 생성
    check_rsi = signal.check_RSI(rsi_df, up_pct=70, donw_pct=30)
    print(check_rsi)
#%%
    # macd값을 이용하여 거래신호 생성
    check_macd = signal.check_MACD(macd_df) # 따로 옵션이 없음
    print(check_macd)
#%%
    # stochastic값을 이용하여 거래신호 생성
    check_stoch = signal.check_STOCH(stoch_df, up_pct=80, down_pct=20)
    print(check_stoch)
#%%
    # 위에서 생성한 거래 신호를 하나의 df로 병합
    signal_df = gathering.merge_all_df(check_bband, check_macd, check_rsi, check_stoch)
    print(signal_df)
#%%
    # 현재 시점에 모든 코스피 정보의 거래 시그널 생성 
    kospi = signal.check_stock(stockmarket=None, item_list=['000660', '005930'], check_date='today', dtype='D')
    print(kospi)
#%%
    # 위에서 생성한 거래 신호를 조합하여 최종 거래 신호를 생성
    # 옵션으로 원하는 지표를 주거나 몇가지의 지표(인자로 준 지표의 개수만 만족하면 됨)를 조합할 것인지 결정
    trade_point = strategy.make_trade_point(signal_df, tech_indicator=['rsi'], indi_count=None)
    print(trade_point)
#%%
    # 볼린져 밴드를 기준으로 원하는 전략을 마켓이나 원하는 주가코드에 대해서 원하는 시점에
    # 거래 시그널을 확인할 수 있다.
    # find_stock = strategy.find_stock_by_bb(strategy=['rsi'], stockmarket='KOSPI', check_date='2010-01-01')
    find_stock = strategy.find_stock_by_bb(strategy=['rsi'], item_list=['000660', '005930'], check_date='2010-01-01', dtype='D')
    print(find_stock)

# %%
