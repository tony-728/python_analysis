import sys
from PyQt5.QtWidgets import *
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
import time
import pandas as pd
import sqlite3

TR_REQ_TIME_INTERVAL = 0.2

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self._create_kiwoom_instance()
        self._set_signal_slots()

    def _create_kiwoom_instance(self): # kiwoom OpenAPI+에 대한 객체 생성하는 메서드
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self): # 이벤트(signal)에 대한 슬롯을 연결을 관리하는 메서드
        self.OnEventConnect.connect(self._event_connect) # 로그인 이벤트에 대한 처리
        self.OnReceiveTrData.connect(self._receive_tr_data) # TR로부터 데이터를 얻어 올때 발생하는 이벤트 처리    
        self.OnReceiveChejanData.connect(self._receive_chejan_data)           

    def comm_connect(self): # OpenAPI+에 로그인하기 위한 메서드 + 이벤트 루프를 만듬 -> 메서드를 호출하면 키움증권의 로그인 창이 나타난다. 
        # OpenAPI+에 함수를 사용하기 위해 dynamicCall 메서드사용
        # OpenAPI+에 로그인하기 위한 메서드 CommConnect()
        self.dynamicCall("CommConnect()") 
        # PyQt의 QEventLoop 클래스 인스턴스를 생성한 후 exec_ 메서드를 호출해 이벤트 루프를 생성한다.
        # 키움증권은 로그인 요청을 받으면 OnEventConnect이벤트를 발생시키는 데 이벤트 루프를 생성했으므로 종료하지 않은 상태로 남아있게 된다.
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        # err_code 값에 따라 연결상태를 화면에 출력
        if err_code == 0:            
            print("connected")
        else:
            print("disconnected")
        # 화면 출력 후 Comm_connect 메서드에서 호출한 이벤트 루프를 종료
        self.login_event_loop.exit()

    def get_code_list_by_market(self, market):  # 종목코드 리스트를 호출하는 메서드
        # OpenAPI+가 제공하는 GetCodeListByMarket 메서드를 dynamicCall 메서드를 이용해서 호출
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market) # GetCodeListByMarket은 시장 번호를 인자로 받는다.
        # GetCodeListByMarket 메서드는 종목코드를 리턴하는데 ;기호를 통해 구분이 되어있어 split 메서드로 구분하여 리스트로 변환
        code_list = code_list.split(';')
        return code_list[:-1]

    def get_master_code_name(self, code): # 종목 코드로 한글 종목명을 얻어오는 메서드
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code) # GetMasterCodeName은 종목코드를 인자로 받는다.
        return code_name

    def get_connect_state(self): # openAPI+에 접속상태를 확인하는 메서드
        ret = self.dynamicCall("GetConnectState()") # 연결 1 미연결 0
        return ret

    def set_input_value(self, id, value): # 키움증권 서버에 TR값을 통신전 값을 입력하기위한 SetInputValue메서드를 호출하기 위한 메서드
        self.dynamicCall("SetInputValue(QString, QString)", id, value) # SetInputValue 첫번째 인자 아이템명(ex)종목코드), 두번째인자 입력값(ex)종목코드값)

    # 키움증권 서버로 TR데이터를 송신하는 메서드
    def comm_rq_data(self, rqname, trcode, next, screen_no):
        # CommRqData의 첫번째 인자 사용자구분명, 두번째 TR명, 세번째 0:조회, 2:연속, 네번째 4자리의 화면번호
        self.dynamicCall("CommRqData(QString, QString, int, QString)", rqname, trcode, next, screen_no)
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    # 키움증권 서버로부터 TR처리에 대한 이벤트가 발생했을때 데이터를 가져오기 위해 CommGetData메서드를 호출하기 위한 메서드
    def _comm_get_data(self, code, real_type, field_name, index, item_name):
        ret = self.dynamicCall("CommGetData(QString, QString, QString, int, QString)", code,
                               real_type, field_name, index, item_name)
        return ret.strip() # 반환받은 문자열 양쪽에 공백이 존재하므로 공백제거

    def _get_repeat_cnt(self, trcode, rqname): # 서버로부터 얻어오는 데이터의 양을 파악하기위한 메서드
        ret = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)
        return ret

    def _receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        # 연속조회시에 한 번에 많은 데이터를 가져올 수 없으므로 next인자의 값을 확인하여 남아있는 데이터를 가져온다.
        if next == '2':
            self.remained_data = True
        else:
            self.remained_data = False

        # rqname인자로 TR요청을 구분하여 처리를 해야한다.
        if rqname == "opt10081_req":
            self._opt10081(rqname, trcode)
        elif rqname == 'opt10082_req':
            self._opt10082(rqname, trcode)
        elif rqname == "opw00001_req":
            self._opw00001(rqname, trcode)
        elif rqname == "opw00018_req":
            self._opw00018(rqname, trcode)
        try:
            # 이 메서드가 호출되었다는 것은 서버로 부터 이벤트가 발생했음을 의미하므로 더 이상 이벤트루프가 필요없기 때문에 종료한다.
            self.tr_event_loop.exit() 
        except AttributeError:
            pass

    # opt10081 TR에 대한 처리 메서드
    def _opt10081(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname) # 데이터를 얻어오기 전에 먼저 데이터의 개수를 얻어온다.

        # 위에서 얻은 개수를 토대로 반복문을 통해서 필요한 데이터를 하나씩 얻어온다. 
        for i in range(data_cnt): 
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

        # opt10082 TR에 대한 처리 메서드, 주봉을 얻어옴
    def _opt10082(self, rqname, trcode):
        data_cnt = self._get_repeat_cnt(trcode, rqname) # 데이터를 얻어오기 전에 먼저 데이터의 개수를 얻어온다.

        # 위에서 얻은 개수를 토대로 반복문을 통해서 필요한 데이터를 하나씩 얻어온다. 
        for i in range(data_cnt): 
            date = self._comm_get_data(trcode, "", rqname, i, "일자")
            open = self._comm_get_data(trcode, "", rqname, i, "시가")
            high = self._comm_get_data(trcode, "", rqname, i, "고가")
            low = self._comm_get_data(trcode, "", rqname, i, "저가")
            close = self._comm_get_data(trcode, "", rqname, i, "현재가")
            volume = self._comm_get_data(trcode, "", rqname, i, "거래량")

            # print(date, open, high, low, close, volume)

            self.ohlcv['date'].append(date)
            self.ohlcv['open'].append(int(open))
            self.ohlcv['high'].append(int(high))
            self.ohlcv['low'].append(int(low))
            self.ohlcv['close'].append(int(close))
            self.ohlcv['volume'].append(int(volume))

    def send_order(self,rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)", 
        [rqname, screen_no, acc_no, order_type, code, quantity, price, hoga, order_no])

    def get_chejan_data(self, fid):
        ret = self.dynamicCall("GetChejanData(int)", fid)
        return ret

    def _receive_chejan_data(self, gubun, item_cnt, fid_list):
        print(gubun)
        print(self.get_chejan_data(9203))
        print(self.get_chejan_data(302))
        print(self.get_chejan_data(900))
        print(self.get_chejan_data(901))

    def get_login_info(self, tag):
        ret = self.dynamicCall("GetLoginInfo(QString)", tag)
        return ret

    def _opw00001(self, rqname, trcode): # 예수금 정보를 조회하는 TR 처리 메서드
        d2_deposit = self._comm_get_data(trcode, "", rqname, 0, "d+2추정예수금")
        self.d2_deposit = Kiwoom.change_format(d2_deposit)

    def _opw00018(self, rqname, trcode):
        # single data
        total_purchase_price = self._comm_get_data(trcode, "", rqname, 0, "총매입금액")
        total_eval_price = self._comm_get_data(trcode, "", rqname, 0, "총평가금액")
        total_eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, 0, "총평가손익금액")
        total_earning_rate = self._comm_get_data(trcode, "", rqname, 0, "총수익률(%)")
        estimated_deposit = self._comm_get_data(trcode, "", rqname, 0, "추정예탁자산")
        
        if self.get_server_gubun(): # 모의투자일 경우 값이 다르게 나오기 때문에 접속서버를 구분하여 데이터를 처리
            total_earning_rate = float(total_earning_rate) / 100
            total_earning_rate = str(total_earning_rate)

        self.opw00018_output['single'].append(Kiwoom.change_format(total_purchase_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_eval_profit_loss_price))
        self.opw00018_output['single'].append(Kiwoom.change_format(total_earning_rate))
        self.opw00018_output['single'].append(Kiwoom.change_format(estimated_deposit))

        # multi data
        rows = self._get_repeat_cnt(trcode, rqname)
        for i in range(rows):
            name = self._comm_get_data(trcode, "", rqname, i, "종목명")
            quantity = self._comm_get_data(trcode, "", rqname, i, "보유수량")
            purchase_price = self._comm_get_data(trcode, "", rqname, i, "매입가")
            current_price = self._comm_get_data(trcode, "", rqname, i, "현재가")
            eval_profit_loss_price = self._comm_get_data(trcode, "", rqname, i, "평가손익")
            earning_rate = self._comm_get_data(trcode, "", rqname, i, "수익률(%)")

            quantity = Kiwoom.change_format(quantity)
            purchase_price = Kiwoom.change_format(purchase_price)
            current_price = Kiwoom.change_format(current_price)
            eval_profit_loss_price = Kiwoom.change_format(eval_profit_loss_price)
            earning_rate = Kiwoom.change_format2(earning_rate)

            self.opw00018_output['multi'].append([name, quantity, purchase_price, current_price, eval_profit_loss_price, earning_rate]) 

    def reset_opw00018_output(self): 
        self.opw00018_output = {'single': [], 'multi':[]} 

    def get_server_gubun(self): # 서버를 구분하기 위해 호출하는 메서드
        ret = self.dynamicCall("KOA_Functions(QString, QString)", "GetServerGubun", "")
        return ret

    @staticmethod
    def change_format(data):
        strip_data = data.lstrip('-0') # 앞쪽에 있는 불필요한 0을 제거함
        if strip_data == '':
            strip_data = '0'

        try:
            format_data = format(int(strip_data), ',d') #정수이면 천단위로 ,를 추가한다.
        except:
            format_data = format(float(strip_data)) # 정수가 아니면 float타입으로 변환

        if data.startswith('-'): # startswith 메서드를 이용해 찾고자하는 문자열의 형태가 앞쪽에 있는지 확인한다.
            format_data = '-' + format_data # 음수인 경우 -기호를 추가한다.
        
        return format_data

    @staticmethod
    def change_format2(data):
        strip_data = data.lstrip('-0')

        if strip_data == '':
            strip_data = '0'
        
        if strip_data.startswith('.'):
            strip_data = '0' + strip_data
        
        if data.startswith('-'):
            strip_data = '-' + strip_data
        
        return strip_data

    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.comm_connect()

    # 시장에 종목코드를 얻어옴
    # code_list = kiwoom.get_code_list_by_market('10') # 10은 코스닥 시장을 의미한다.
    # for code in code_list:
    #     print(code, end=" ")

    # 종목코드로 한글종목명을 얻어옴
    # print(kiwoom.get_master_code_name("000660"))

    # opt10081 TR 요청, 처음에 한 번 요청을 하고 
    # kiwoom.set_input_value("종목코드", "039490")
    # kiwoom.set_input_value("기준일자", "20170224")
    # kiwoom.set_input_value("수정주가구분", 1)
    # kiwoom.comm_rq_data("opt10081_req", "opt10081", 0, "0101")

    # while kiwoom.remained_data == True:
    #     time.sleep(TR_REQ_TIME_INTERVAL) # 키움증권은 1초에 최대 5번의 TR요청을 허용하므로 대기시간을 조절
    #     kiwoom.set_input_value("종목코드", "039490")
    #     kiwoom.set_input_value("기준일자", "20170224")
    #     kiwoom.set_input_value("수정주가구분", 1)
    #     kiwoom.comm_rq_data("opt10081_req", "opt10081", 2, "0101")

    kiwoom.set_input_value("종목코드", "039490")
    kiwoom.set_input_value("기준일자", "20170224")
    kiwoom.set_input_value("수정주가구분", 1)
    kiwoom.comm_rq_data("opt10082_req", "opt10082", 0, "0101")

    while kiwoom.remained_data == True:
        time.sleep(TR_REQ_TIME_INTERVAL) # 키움증권은 1초에 최대 5번의 TR요청을 허용하므로 대기시간을 조절
        kiwoom.set_input_value("종목코드", "039490")
        kiwoom.set_input_value("기준일자", "20170224")
        kiwoom.set_input_value("수정주가구분", 1)
        kiwoom.comm_rq_data("opt10082_req", "opt10082", 2, "0101")

    # 예수금 정보 조회
    # kiwoom.set_input_value("계좌번호", "8129063311")
    # kiwoom.set_input_value("비밀번호", "0000")
    # kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

    # print(kiwoom.d2_deposit)

    # 잔고 조회
    # account_number = kiwoom.get_login_info("ACCNO")
    # account_number = account_number.split(';')[0]

    # kiwoom.set_input_value("계좌번호", account_number)
    # kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

