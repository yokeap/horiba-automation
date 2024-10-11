import sys
import autoit
import time
import pyautogui
import threading
from datetime import datetime

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow



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
        # bootup process
        time.sleep(10) 
        try:
            pyautogui.click('./imgdata/_0_btCancel.png')
        except pyautogui.ImageNotFoundException:
            print('Error: Start program')
            # send error to arduino

    def process(self):
        
        ################ project open process ###################
        time.sleep(1) 
        try:
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(1) 
            pyautogui.click('./imgdata/_1_ltProjectOpen.png', clicks=2)
        except pyautogui.ImageNotFoundException:
            print('Error: project open')
        

        ################# run egat cal curve ####################
        time.sleep(2) 
        try:
            pyautogui.click('./imgdata/_2_btEGATCal.png')
            time.sleep(300) 
            # runState = pyautogui.locateOnScreen('calc7key.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot run')

        ################## report process #######################
        time.sleep(1) 
        try:
            pyautogui.click('./imgdata/_3_btReport.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot report')

        ################## save process #########################
        time.sleep(3) 
        try:
            pyautogui.click('./imgdata/_4_btExport.png')
            time.sleep(1) 
            pyautogui.click('./imgdata/_5_ddExcel.png')
            autoit.win_wait_active("[CLASS:Save As]", 3)
            autoit.control_send("[CLASS:Save As]", 1001, "D:\SaveTemp")
            saveDT = "Report" + datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
            autoit.control_send("[CLASS:Save As]", "Edit", saveDT)
            autoit.control_click("[CLASS:Save As]", "Button2")
        except pyautogui.ImageNotFoundException:
            print('Error: cannot export')

        except autoit.autoit.AutoItError:
            print('Error: cannot save')

        ##################### close ############################
        time.sleep(1) 
        try:
            pyautogui.click('./imgdata/_6_btClose.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot report')
    
    def run(self, stop_event):
        while not stop_event.is_set():
            self.process()

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
  
        # printing pressed 
        # autoit.run("MESA.exe")
        self.mesaApp = Mesa()
        self.stop_event = threading.Event()
        self.mesaThread = threading.Thread(target=self.mesaApp.run, args=(self.stop_event,))

        self.mesaThread.start()
        print("pressed") 

    def clickStop(self):
        # self.mesaThread.terminate() 
        self.stop_event.set()
        # printing pressed 
        # print("pressed") 


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()