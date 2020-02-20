import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import uic # Qt Designer로 만든 .ui 파일을 사용하기 위해 임포트
from Kiwoom import *
from sh1 import * 

form_class = uic.loadUiType("2020-파이썬분석팀/Kiwoom/pytrader.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

        self.sh1 = SH_trader()

        # Timer1
        self.timer = QTimer(self)
        self.timer.start(1000)
        self.timer.timeout.connect(self.timeout)

        # 종목 코드를 입력하면(이벤트) 종목명을 출력하도록 이벤트와 슬롯을 연결
        self.lineEdit.textChanged.connect(self.code_changed)

        # 키움서버로 부터 계좌정보를 얻어옴
        accouns_num = int(self.kiwoom.get_login_info("ACCOUNT_CNT")) # 계좌 개수
        accounts = self.kiwoom.get_login_info("ACCNO") # 계좌 정보
        accounts_list = accounts.split(';')[0:accouns_num]
        self.comboBox.addItem(accounts_list[0])

        # 현금주문 버튼을 누르면 주문이 보내지도록 이벤트와 슬롯을 연결
        self.pushButton.clicked.connect(self.send_order)
        # 조회 버튼을 누르면 잔고및 보유현황을 보여주도록 이벤트와 슬롯을 연결
        self.pushButton_2.clicked.connect(self.check_balance)

        #Timer2
        self.timer2 = QTimer(self)
        self.timer2.start(1000*10)
        self.timer2.timeout.connect(self.timeout2)

        self.load_buy_sell_list()

        self.trade_stocks_done = False
        
        # 선정 버튼을 누르면 해당 종류의 종목으로 선정을 하도록 이벤트와 슬롯을 연결
        self.pushButton_3.clicked.connect(self.make_buy_sell_list)
        # 자동선정종목리스트의 조회를 누르면 해당 종목을 출력하도록 이벤트와 슬롯을 연결
        self.pushButton_4.clicked.connect(self.load_buy_sell_list)

        self.pushButton_5.clicked.connect(self.save_csvfile)

    def timeout(self):
        market_start_time = QTime(9,0,0)
        current_time = QTime.currentTime()

        if current_time > market_start_time and self.trade_stocks_done is False:
            self.trade_stocks()
            self.trade_stocks_done = True    
        
        text_time = current_time.toString("hh:mm:ss")
        time_msg = "현재시간: " + text_time

        state = self.kiwoom.get_connect_state()
        if state == 1:
            state_msg = "서버 연결 중"
        else:
            state_msg = "서버 미 연결 중"

        self.statusbar.showMessage(state_msg + " | " + time_msg)

    def timeout2(self):
        if self.checkBox.isChecked():
            self.check_balance()

    def code_changed(self):
        code = self.lineEdit.text()
        name = self.kiwoom.get_master_code_name(code)
        self.lineEdit_2.setText(name)

    def send_order(self):
        # 실제 키움API에는 세부 항목에 대응되는 정숫값이 전될돼야 한다.
        order_type_lookup = {'신규매수': 1, '신규매도': 2, '매수취소': 3, '매도취소': 4}
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        account = self.comboBox.currentText() 
        order_type = self.comboBox_2.currentText()
        code = self.lineEdit.text()
        hoga = self.comboBox_3.currentText()
        volume = self.spinBox.value()
        price = self.spinBox_2.value()

        self.kiwoom.send_order("send_order_req", "0101", account, order_type_lookup[order_type], code, volume, price, hoga_lookup[hoga], "")

    def check_balance(self):
        self.kiwoom.reset_opw00018_output()
        account_number = self.kiwoom.get_login_info("ACCNO")
        account_number = account_number.split(';')[0]

        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 0, "2000")

        while self.kiwoom.remained_data: # 연속조회일 경우 반복해서 TR을 요청
            time.sleep(0.2)
            self.kiwoom.set_input_value("계좌번호", account_number)
            self.kiwoom.comm_rq_data("opw00018_req", "opw00018", 2, "2000")

        # opw00001, 예수금 데이터를 얻기 위한 TR
        self.kiwoom.set_input_value("계좌번호", account_number)
        self.kiwoom.comm_rq_data("opw00001_req", "opw00001", 0, "2000")

        # balance
        item = QTableWidgetItem(self.kiwoom.d2_deposit)
        item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight) # 정렬
        self.tableWidget.setItem(0, 0, item) # QTableWidget에 적절한 위치(0,0)에 넣는다.

        for i in range(1, 6): # 총매입, 총평가, 총손익, 총수익률, 추정자신을 QTableWidget의 컬럼에 추가
            item = QTableWidgetItem(self.kiwoom.opw00018_output['single'][i - 1])
            item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
            self.tableWidget.setItem(0, i, item)

        self.tableWidget.resizeRowsToContents() # 아이템의 크기에 맞춰 행의 높이를 조절

        # Item list, 보유 종목별 평가 잔고 데이터를 QTableWidget에 추가
        item_count = len(self.kiwoom.opw00018_output['multi'])
        self.tableWidget_2.setRowCount(item_count) # 보유종목의 개수를 확인한 후 개수를 설정, 열의 개수는 Qt Designer에서 자동으로 설정했음

        for j in range(item_count):
            row = self.kiwoom.opw00018_output['multi'][j]
            for i in range(len(row)):
                item = QTableWidgetItem(row[i])
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignRight)
                self.tableWidget_2.setItem(j, i, item)

        self.tableWidget_2.resizeRowsToContents() # 행의 크기를 조절

    def load_buy_sell_list(self):
        f = open("2020-파이썬분석팀/Kiwoom/buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("2020-파이썬분석팀/Kiwoom/sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        row_count = len(buy_list) + len(sell_list)
        self.tableWidget_3.setRowCount(row_count)

        # buy list
        for j in range(len(buy_list)):
            row_data = buy_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rsplit())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(j, i, item)

        # sell list
        for j in range(len(sell_list)):
            row_data = sell_list[j]
            split_row_data = row_data.split(';')
            split_row_data[1] = self.kiwoom.get_master_code_name(split_row_data[1].rstrip())

            for i in range(len(split_row_data)):
                item = QTableWidgetItem(split_row_data[i].rstrip())
                item.setTextAlignment(Qt.AlignVCenter | Qt.AlignCenter)
                self.tableWidget_3.setItem(len(buy_list) + j, i, item)

        self.tableWidget_3.resizeRowsToContents()

    # 각 거래일의 장 시작에 맞춰 주문 방식에 따라 주문을 자동수행
    def trade_stocks(self):
        hoga_lookup = {'지정가': "00", '시장가': "03"}

        f = open("2020-파이썬분석팀/Kiwoom/buy_list.txt", 'rt')
        buy_list = f.readlines()
        f.close()

        f = open("2020-파이썬분석팀/Kiwoom/sell_list.txt", 'rt')
        sell_list = f.readlines()
        f.close()

        # account
        account = self.comboBox.currentText()

        # buy list
        for row_data in buy_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매수전':
                self.kiwoom.send_order("send_order_req", "0101", account, 1, code, num, price, hoga_lookup[hoga], "")

        # sell list
        for row_data in sell_list:
            split_row_data = row_data.split(';')
            hoga = split_row_data[2]
            code = split_row_data[1]
            num = split_row_data[3]
            price = split_row_data[4]

            if split_row_data[-1].rstrip() == '매도전':
                self.kiwoom.send_order("send_order_req", "0101", account, 2, code, num, price, hoga_lookup[hoga], "")

        # buy list
        for i, row_data in enumerate(buy_list):
            buy_list[i] = buy_list[i].replace("매수전", "주문완료")

        # file update
        f = open("2020-파이썬분석팀/Kiwoom/buy_list.txt", 'wt')
        for row_data in buy_list:
            f.write(row_data)
        f.close()

        # sell list
        for i, row_data in enumerate(sell_list):
            sell_list[i] = sell_list[i].replace("매도전", "주문완료")

        # file update
        f = open("2020-파이썬분석팀/Kiwoom/sell_list.txt", 'wt')
        for row_data in sell_list:
            f.write(row_data)
        f.close()

    def make_buy_sell_list(self):
        codes = self.sh1.get_stockcode('KOSDAQ')
        codes_list = list(codes.Symbol)

        price_df = self.sh1.get_stock_data(codes_list, startdate='2019-12-01')

        make_type = self.comboBox_4.currentText()

        if make_type == '정배열/역배열':        
            arr = self.sh1.check_arr(codes_list, startdate='2019-12-01')
            rarr =self.sh1.check_rarr(codes_list, startdate='2019-12-01') 
            print(arr, rarr)   

        return         

    def save_csvfile(self):
        codes = self.sh1.get_stockcode('KOSDAQ')
        codes_list = list(codes.Symbol)

        price_df = self.sh1.get_stock_data(codes_list, startdate='2019-12-01')

        make_type = self.comboBox_4.currentText()

        if make_type == '정배열/역배열':        
            arr = self.sh1.check_arr(codes_list, startdate='2019-12-01', filetype='csv')
            rarr =self.sh1.check_rarr(codes_list, startdate='2019-12-01', filetype='csv') 
            print(arr, rarr)   

        return         

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    app.exec_()