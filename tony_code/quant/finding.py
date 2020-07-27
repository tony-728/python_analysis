from stock_signal import check_stock
from strategy import make_trade_point

'''
로그: 2020.03.11 시작
파라미터: 전략, 주식마켓 또는 주식코드리스트, 확인 할 날짜, 기준시간(일봉 or 주봉)
기능: 오늘기준으로 전략에 해당하는 주식 추출하기
리턴: 데이터프레임에 실제 매수매도 시그널을 생성    '''
# 함수포인터를 파라미터로 받을 수 있게 조정... 함수 포인터를 받을 수 없나..?
def find_stock_by_bb(strategy, stockmarket=None, item_list=None, check_date='today', dtype='D'):
    df = check_stock(stockmarket=stockmarket, item_list=item_list, check_date=check_date, dtype=dtype)
    result = make_trade_point(df, strategy)

    return result 