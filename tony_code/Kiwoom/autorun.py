from pywinauto import application
from pywinauto import timings
import time
import os

# 프로그램을 자동으로 실행
app = application.Application()
app.start("C:/KiwoomFlash3/bin/nkministarter.exe") 

title = "번개3 Login"
# 키움 번개 로그인 대화상자를 dlg라는 변수로 바인딩함
dlg = timings.WaitUntilPasses(20, 0.5, lambda: app.window_(title=title))

# dlg로 부터 비밀번호와 인증비밀번호를 입력하는 데 사용되는 컨트롤을 구함
# Edit2, Edit3 Button0는 SWAPY프로그램을 이용해 윈도우 대화상자 및 컨트롤에 대한 정보를 얻음
pass_ctrl = dlg.Edit2 
pass_ctrl.SetFocus() # SetFocus메서드로 선택
pass_ctrl.TypeKeys('ksh0728') # 비밀번호 입력

cert_ctrl = dlg.Edit3
cert_ctrl.SetFocus()
cert_ctrl.TypeKeys('ksh2030313!@') # 인증비밀번호 입력

btn_ctrl = dlg.Button0
btn_ctrl.Click() 

time.sleep(70) # 키움 번개3가 버전업데이트하는 동안 기다림
# 키움 번개3는 버전업데이트를 하는데만 필요하므로 종료
# 윈도우에서는 taskkill 명령을 이용해 특정 프로그램을 종료할 수 있다. 
os.system("taskkill /im nkmini.exe") 