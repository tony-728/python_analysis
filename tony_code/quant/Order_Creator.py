from Gathering import *
from Tech_Indi import *
from Signal import *
from Strategy import *
import re
import copy

gathering = Gathering()
techIndi = TechIndi()
signal = Signal()

class OrderCreator:
    '''
    로그: 2020.7.19 시작
    기능: 주가데이터로부터 볼린져밴드 값과 볼린져 밴드기반에 전략(기본전략)에 필요한 시그널을 구함
    파라미터: 주가데이터프레임, 이동평균기간, 표준편차의 상향값, 표준편차의 하향값, 캔들 상승비율, 캔들 하락비율, 과거를 볼 기간
    리턴: 볼린져밴드 기반에 거래신호 데이터프레임   '''
    def BBcandle(self, df, period=10, nbdevup=2, nbdevdn=2, up_pct=2.0, down_pct=0.5, check_period=2):
        bbcandle_df = techIndi.get_BBand(df=df, period=period, nbdevup=nbdevup, nbdevdn=nbdevdn,
                                        up_pct=up_pct, down_pct=down_pct)
        check_bband = signal.check_bbcandle(bbcandle_df, period=check_period) # 현재포함 과거 2일을 확인

        return check_bband

    '''
    로그: 2020.7.19 시작
    파라미터: 주가 데이터프레임, RSI를 확인할 기간, RSI을 판단할 percentage
    기능: RSI 지표 생성과 RSI 지표 기반에 거래신호를 생성한다.
    리턴: RSI기반에 거래신호 데이터프레임'''
    def RSI(self, df, timeperiod=14):  #, up_pct=70, donw_pct=30
        rsi_df = techIndi.get_RSI(df=df, timeperiod=timeperiod)
        # check_rsi = signal.check_RSI(rsi_df, up_pct=up_pct, donw_pct=donw_pct)

        return rsi_df

    '''
    로그: 2020.7.19 시작
    파라미터: 주가 데이터프레임, 단기이평기간, 장기이평기간, 단기-장기 값의 이평의 이평기간
    기능: MACD값을 생성하고 MACD<0이면 거래신호를 생성하지 않는다.
    리턴: MACD기반에 거래신호 데이터 프레임   '''
    def MACD(self, df, fast_period=12, slow_period=26, signal_period=9):
        macd_df = techIndi.get_MACD(df=df, fast_period=fast_period,
                                    slow_period=slow_period, signal_period=signal_period)
        check_macd = signal.check_MACD(macd_df) # 따로 옵션이 없음

        return check_macd

    '''
    로그: 2020.7.19 시작
    파라미터: 주가 데이터프레임, 전체 기간(fastk_period,N), Fask %D, slow %K의 이평기간(slowk_period, M), slow %D의 이평기간(slowd_period, T)
    기능: 스토케스틱 지표를 생성하고 지표 기반에 거래신호를 생성한다.
    리턴: 스토케스틱 기반에 거래신호 데이터 프레임    '''
    def STOCH(self, df, fastk_period=5, slowk_period=3, slowd_period=3, up_pct=80, down_pct=20, case=1):
        stoch_df = techIndi.get_STOCH(df=df, fastk_period=fastk_period,
                                        slowk_period=slowk_period, slowd_period=slowd_period)
        check_stoch = signal.check_STOCH(stoch_df, up_pct=up_pct, down_pct=down_pct, case=case)

        return check_stoch

    '''
    로그: 2020.7.20 시작 2020.7.22 수정
    파라미터: 파일의 내용
    기능: 읽은 파일에서 주가정보를 생성하기 위한 데이터를 정제하고, 기술적지표와 전략을 생성하는 인덱스를 찾는다.
    리턴: 주가정보를 생성하기 위한 데이터(주가코드, 시작날짜, 끝날짜, 데이터타입), 기술적지표와 전략의 시작 인덱스 '''
    def split_order(self, file_contents):
        lines = file_contents.readlines()
        for idx, line in enumerate(lines):
            line = line.replace('\n', '')
            if idx < 4:
                if(line.find('stockcode') != -1):
                    code = line.split('=')
                    code = code[-1].strip() # .replace('\n', '')
                
                elif(line.find('startdate') != -1):
                    startdate = line.split('=')
                    startdate = startdate[-1].strip() # .replace('\n', '')
                    
                elif(line.find('enddate') != -1):
                    enddate = line.split('=')
                    enddate = enddate[-1].strip() # .replace('\n', '')
                    
                elif(line.find('dtype') != -1):
                    dtype = line.split('=')
                    dtype = dtype[-1].strip() # .replace('\n', '')

            else:
                if line == '':
                    continue
                else:
                    # print(line)
                    if line == '<make_tech>':
                        # print(idx)
                        make_tech_idx = idx+1        

                    elif line == '<make_strategy>':
                        # print(idx)
                        make_order_idx = idx+1
                
        return code, startdate, enddate, dtype, lines, make_tech_idx, make_order_idx

    '''
    로그: 2020.7.22 시작
    파라미터: 파일의 내용, 주가데이터프레임, 기술적지표 시작인덱스, 전략 시작인덱스
    기능: 읽은 파일에서 기술적지표에 해당되는 내용을 실행시켜 기술적지표 값(또는 판단 기준)을 생성한다.
    리턴: 주가데이터와 기술적지표 값(또는 판단기준) 컬럼이 존재하는 데이터프레임 '''
    def make_tech(self, file_contents, df, tech_idx, order_idx):
        f = copy.deepcopy(file_contents)
        techs = []
        for i in range(tech_idx, order_idx-1):
            line = f[i].replace('\n', '')
            if line != '':            
                line = line.replace('(', '(df,')
                # print(line)
                techs.append(line)

        for idx, tech in enumerate(techs):
            if idx == 0:
                fir_df = eval('self.'+tech)
            else:
                snd_df = eval('self.'+tech)
                fir_df = gathering.merge_all_df(fir_df, snd_df)

        fir_df = gathering.merge_all_df(fir_df, df)

        fir_df.drop(['volume', 'change', 'ubb', 'mbb', 'lbb'], axis='columns', inplace=True)

        return fir_df

    '''
    로그: 2020.7.22 시작
    파라미터: 파일의 내용, 전략 시작인덱스
    기능: 파일의 전략 조건과 조건이 만족할 때 실행되는 문자열로 나눈다.
    리턴: 전략 조건과 주문 함수의 리스트 '''
    def make_strategy(self, file_contents, order_idx):
        f = copy.deepcopy(file_contents)
        order_list = []
        for i in range(order_idx, len(f)):
            line = f[i].replace('\n', '')
            if line != '':
                order_list.append(line.replace('if ', '').split(':'))

        return order_list

    '''
    로그: 2020.7.22 시작
    파라미터: 전략정보가 담긴 리스트, 기술적지표 값(또는 판단시그널)이 포함된 주가 데이터 프레임, 주가 코드
    기능: 전략이 만족할 때 buy(sell)함수를 호출한다.
    리턴: buy(sell)함수로 부터 리턴받은 정보(리스트)를 json형식으로 리턴한다. '''
    def make_trading(self, order_list, trade_df, code):
        trade_list=[]
        trades = copy.deepcopy(trade_df)
        trades = trades.reset_index() # 날짜데이터가 인덱스이므로 컬럼으로 바꿈 -> row에 정보를 넣기 위해서
        trades['Date'] = trades['Date'].apply(lambda x: x.strftime('%Y-%m-%d')) # json파일에서 datetime형식은 깨지므로 문자열로 변환

        df_krx = fdr.StockListing('KRX')
        name = df_krx.loc[df_krx.Symbol == code, 'Name'].values[0] # 주가 코드에 해당하는 이름을 찾음

        # 주가 데이터프레임에 주가 코드, 이름을 추가
        trades['code'] = code
        trades['code_name'] = name

        for order in order_list:
            for _, trade in trades.iterrows():            
                if eval(order[0]): # if trade.rsi > 70 & trade.bbcandle_buy:
                    order_data = eval('self.' + order[1].replace(' ','').replace('(', '(trade,')) # buy(trade, stock)
                    trade_list.append(order_data)
        
        # 리스트를 데이터프레임로 변환
        result_df = pd.DataFrame(trade_list, columns=['order_datetime', 'order_type', 'item_code', 'item_name', 
                                                        'order_price', 'order_option', 'order_value'])

        # 데이터프레임을 json파일로 변환
        result_json = result_df.to_json(orient='records', force_ascii=False)

        return result_json

    '''
    로그: 2020.7.22 시작
    파라미터: 주가데이터프레임의 행, 거래할 주식의 수
    기능: 입력한 데이터프레임의 행과 주식의 수, 코드정보를 필요한 정보만 정제해서 리스트로 만든다.
    리턴: 정제한(날짜, 거래종류, 주가코드, 주가이름, 거래가격, 거래할 주식의 수(또는 전쳬)) 리스트 '''
    def buy(self, trade_row, stock):
        buy_list = []    
        if type(stock) is int:
            buy_list.extend([trade_row.Date, 'buy', trade_row.code, trade_row.code_name, trade_row.close, 'scnt', str(stock)])
        else:
            buy_list.extend([trade_row.Date, 'buy', trade_row.code, trade_row.code_name, trade_row.close, 'scnt', 'all'])

        return buy_list

    '''
    로그: 2020.7.22 시작
    파라미터: 주가데이터프레임의 행, 거래할 주식의 수
    기능: 입력한 데이터프레임의 행과 주식의 수, 코드정보를 필요한 정보만 정제해서 리스트로 만든다.
    리턴: 정제한(날짜, 거래종류, 주가코드, 주가이름, 거래가격, 거래할 주식의 수(또는 전쳬)) 리스트 '''
    def sell(self, trade_row, stock):
        sell_list = []
        if type(stock) is int:
            sell_list.extend([trade_row.Date, 'sell', trade_row.code, trade_row.code_name, trade_row.close, 'scnt', str(stock)])
        else:
            sell_list.extend([trade_row.Date, 'sell', trade_row.code, trade_row.code_name, trade_row.close, 'scnt', 'all'])

        return sell_list


if __name__ == "__main__":
    gathering = Gathering()
    techIndi = TechIndi()
    signal = Signal()
    ordercreate = OrderCreator()

    f = open('2020-파이썬분석팀/QUANT/user_test.txt', 'r')
    # f = open('user_test.txt', 'r')

    code, startdate, enddate, dtype, f, tech_idx, order_idx = ordercreate.split_order(f)

    # print(code)
    # print(startdate)
    # print(enddate)
    # print(dtype)

    df = gathering.get_stock(code=code, startdate=startdate, enddate=enddate, dtype=dtype)
    # print(df)

    trade_df = ordercreate.make_tech(f, df, tech_idx, order_idx)
    # print(trade_df)

    order_list = ordercreate.make_strategy(f, order_idx)
    # print(order_list)

    order_json = ordercreate.make_trading(order_list=order_list, trade_df=trade_df, code=code)
    print(order_json)
