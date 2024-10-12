import os
import subprocess
import sys
import autoit
import time
import pyautogui
import threading
import pyuac
from datetime import datetime

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow

stop_event = threading.Event()

# app = QApplication(sys.argv)

# # Create a Qt widget, which will be our window.
# window = QWidget()
# window.setWindowTitle("Horiba Automate")
# # window.setGeometry(100, 100, 380, 480)
# layout = QVBoxLayout()
# layout.addWidget(QLabel("<h1>Horiba Automate System</h1>", parent=window))
# layout.addWidget(QPushButton("Start"))
# layout.addWidget(QPushButton("Stop"))
# window.setLayout(layout)
# window.show()  # IMPORTANT!!!!! Windows are hidden by default.

# # Start the event loop.
# app.exec()

class Mesa():
    def __init__(self):
        super().__init__()
        self.init = True
        # bootup process
        time.sleep(10) 
        try:
            pyautogui.click('./imgdata/_0_btCancel.png')
        except pyautogui.ImageNotFoundException:
            print('Error: Start program')
            self.init = False

        ################ project open process ###################
        time.sleep(1)
        try:
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(1) 
            pyautogui.click('./imgdata/_1_ltProjectOpen.png', clicks=2)
        except pyautogui.ImageNotFoundException:
            print('Error: project open')
            self.init = False
        
            # send error to arduino

    def process(self,stop_event):
        
        ################# run egat cal curve ####################
        time.sleep(2) 
        try:
            pyautogui.click('./imgdata/_2_btEGATCal.png')       
            # runState = pyautogui.locateOnScreen('calc7key.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot run')
            return False

        ################# check success #######################
        time.sleep(10) 
        elapsed = 0
        start = time.time()
        flagSuccess = False
        while elapsed < 300:
            try:
                # time.sleep(10) 
                done = time.time()
                elapsed = done - start
                ready = pyautogui.locateOnScreen('./imgdata/_2_1_ready.png')
                if ready:
                    elapsed = 310
                    flagSuccess = True              
            except pyautogui.ImageNotFoundException:
                print('Wait for process.')

        if(flagSuccess == False):
            print("incompleted")
            return False


        ################## report process #######################
        time.sleep(1) 
        try:
            pyautogui.click('./imgdata/_3_btReport.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot report')
            return False

        ################## save process #########################
        time.sleep(3) 
        try:
            pyautogui.click('./imgdata/_4_btExport.png')
            time.sleep(1) 
            pyautogui.click('./imgdata/_5_ddExcel.png')
            autoit.win_wait_active("Save As", 3)
            time.sleep(1) 
            # autoit.control_click("Save As", "Address Band Root1")
            # autoit.control_send("Save As", "Address Band Root1", "D:\Data")
            saveDT = "Report" + datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
            autoit.control_send("Save As", "Edit1", saveDT)
            time.sleep(1) 
            autoit.control_click("Save As", "Button2")
        except pyautogui.ImageNotFoundException as e:
            print(e)
            return False

        except autoit.autoit.AutoItError as e:
            print(e)
            return False

        ##################### close ############################
        time.sleep(1) 
        try:
            pyautogui.click('./imgdata/_6_btClose.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot report')
            return False
    
    def run(self, stop_event):
        while not stop_event.is_set():
            if self.process(stop_event) == False:
                stop_event.set()
                print("Thread stop!")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Horiba Automate")
        self.setFixedSize(QSize(180, 280))

        self.layout = QVBoxLayout(self)

        # calling method 
        self.UiComponents(self.layout) 
  

    # method for widgets 
    def UiComponents(self, layout): 
        
        label = QLabel("<h1>Horiba</h1>")
        label1 = QLabel("<h1>Automate</h1>")
        label2 = QLabel("<h1>System</h1>")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label1, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label2, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # creating a push button 
        btStart = QPushButton("Start", self) 
        btStop = QPushButton("Stop", self) 
  
        # setting size of button 
        btStart.setFixedSize(100, 60)
        btStop.setFixedSize(100, 60)
        
        layout.addWidget(btStart, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(btStop, alignment=Qt.AlignmentFlag.AlignCenter)
  
        # adding action to a button 
        btStart.clicked.connect(self.clickStart) 
        btStop.clicked.connect(self.clickStop) 
  
  
    # action method 
    def clickStart(self): 
        os.chdir(r"C:\Program Files (x86)\HORIBA\HORIBA X-RAY LAB For MESA-50 SERIES")
        subprocess.Popen("MesaApplication.exe")
        os.chdir(r"D:\software\horiba-automation-main")
        self.mesaApp = Mesa()
        if self.mesaApp.init == True:
            self.stop_event = threading.Event()
            self.mesaThread = threading.Thread(target=self.mesaApp.run, args=(self.stop_event,))
            self.mesaThread.daemon = True
            self.mesaThread.start()
        else:
            print("Mesa Initilization fail")

    def clickStop(self):
        # self.mesaThread.terminate() 
        stop_event.set()
        sys.exit()
        # printing pressed 
        print("stop thread") 


if __name__ == "__main__":
    # if not pyuac.isUserAdmin():
    #     print("Re-launching as admin!")
    #     pyuac.runAsAdmin()
    # else:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()