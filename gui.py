import os
import subprocess
import sys
import autoit
import time
import pyautogui
import threading
import pyuac
from datetime import datetime
from src import mesa

from PyQt5.QtCore import QSize, Qt, pyqtSlot, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo

# class mesa(QObject):
#     data_received = pyqtSignal(str)

#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.serial_port = QSerialPort()
#         self.serial_port.readyRead.connect(self.on_ready_read)
#         self.open_port("COM4")
        
#         self.serialReceive = 0
#         self.init = False
#         self.pcc_status = False

#         self.stop_event = threading.Event()
#         n=0
#         self.write_data("MESA,CHK\n")
#         # while n < 3:
#         #     if self.serialReceive == "MESA,RDY":
#         #         self.serialReceive = ""
#         #         self.init = True
#         #         n = 3
#         #     time.sleep(1)
#         #     n++ 

#         self.mesaThread = threading.Thread(target=self.run)
#         self.mesaThread.daemon = True
#         self.init = True
    
#     def open_port(self, port_name):
#         if self.serial_port.isOpen():
#             self.serial_port.close()
#         self.serial_port.setPortName(port_name)
#         # self.serial_port.setBaudRate(9600)
#         # self.serial_port.setDataBits(QSerialPort.DataBits.Data8)
#         # self.serial_port.setParity(QSerialPort.Parity.NoParity)
#         # self.serial_port.setStopBits(QSerialPort.StopBits.OneStop)
#         # self.serial_port.open(QSerialPort.OpenModeFlag.ReadWrite)
#         self.serial_port.setBaudRate(QSerialPort.Baud9600)
#         self.serial_port.setDataBits(QSerialPort.Data8)
#         self.serial_port.setParity(QSerialPort.NoParity)
#         self.serial_port.setStopBits(QSerialPort.OneStop)
#         self.serial_port.open(QSerialPort.ReadWrite)

#     @pyqtSlot()
#     def write_data(self, data):
#         print(data)
#         if self.serial_port.isOpen():
#             print(data.encode())
#             self.serial_port.writeData(data.encode())

#     @pyqtSlot()
#     def on_ready_read(self):
#         if self.serial_port.canReadLine():
#             # print(str(self.serial_port.readLine()))
#             data = self.serial_port.readLine().data().decode().strip()      
#             # print(data)   
#             self.serialReceive = data
#             # self.data_received.emit(data)

#     def start(self):
#         # bootup process
#         time.sleep(10) 
#         try:
#             pyautogui.click('./imgdata/_0_btCancel.png')
#         except pyautogui.ImageNotFoundException:
#             print('Error: Start program')
#             self.write_data("MESA,ALM\n")
#             return False

#         ################ project open process ###################
#         time.sleep(1)
#         try:
#             pyautogui.hotkey('ctrl', 'o')
#             time.sleep(1) 
#             pyautogui.click('./imgdata/_1_ltProjectOpen.png', clicks=2)
#         except pyautogui.ImageNotFoundException:
#             print('Error: project open')
#             self.write_data("MESA,ALM\n")
#             return False
#         return True
        

#     def process(self):
        
#         ################# run egat cal curve ####################
#         time.sleep(2) 
#         self.write_data("MESA,MSR\n")
#         try:
#             pyautogui.click('./imgdata/_2_btEGATCal.png')       
#             # runState = pyautogui.locateOnScreen('calc7key.png')
#         except pyautogui.ImageNotFoundException:
#             print('Error: cannot run')
#             self.write_data("MESA,ALM\n")
#             return False

#         ################# check success #######################
#         time.sleep(10) 
#         elapsed = 0
#         start = time.time()
#         flagSuccess = False
#         while elapsed < 300:
#             try:
#                 # time.sleep(10) 
#                 done = time.time()
#                 elapsed = done - start
#                 ready = pyautogui.locateOnScreen('./imgdata/_2_1_ready.png')
#                 if ready:
#                     elapsed = 310
#                     flagSuccess = True              
#             except pyautogui.ImageNotFoundException:
#                 print('Wait for process.')

#         if(flagSuccess == False):
#             print("incompleted")
#             self.write_data("MESA,ALM\n")
#             return False


#         ################## report process #######################
#         time.sleep(1) 
#         try:
#             pyautogui.click('./imgdata/_3_btReport.png')
#         except pyautogui.ImageNotFoundException:
#             print('Error: cannot report')
#             self.write_data("MESA,ALM\n")
#             return False

#         ################## save process #########################
#         time.sleep(3) 
#         try:
#             pyautogui.click('./imgdata/_4_btExport.png')
#             time.sleep(1) 
#             pyautogui.click('./imgdata/_5_ddExcel.png')
#             autoit.win_wait_active("Save As", 3)
#             time.sleep(1) 
#             # autoit.control_click("Save As", "Address Band Root1")
#             # autoit.control_send("Save As", "Address Band Root1", "D:\Data")
#             saveDT = "Report" + datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
#             autoit.control_send("Save As", "Edit1", saveDT)
#             time.sleep(1) 
#             autoit.control_click("Save As", "Button2")
#         except pyautogui.ImageNotFoundException as e:
#             print(e)
#             self.write_data("MESA,ALM\n")
#             return False

#         except autoit.autoit.AutoItError as e:
#             print(e)
#             self.write_data("MESA,ALM\n")
#             return False

#         ##################### close ############################
#         time.sleep(1) 
#         try:
#             pyautogui.click('./imgdata/_6_btClose.png')
#         except pyautogui.ImageNotFoundException:
#             print('Error: cannot report')
#             self.write_data("MESA,ALM\n")
#             return False  
#         self.write_data("MESA,MSD\n")

#     def run(self):
#         self.pcc_status = False
#         while not self.stop_event.is_set():
#             if self.serialReceive == "MESA,MS":
#                 print(self.serialReceive)
#                 self.serialReceive = ""
#                 self.pcc_status = self.process()
#                 if self.pcc_status == False:
#                     self.stop_event.set()
#                     print("Thread stop!") 
#                     return False
                

#     def start_thread(self):        
#         self.mesaThread.start()

#     def stop_thread(self):
#         self.stop_event.set()

#     # @pyqtSlot(str)
#     # def on_data_received(self, data):
#     #     print("pyqtslot: ")
#     #     print(data) 
#     #     self.serialReceive = data

class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.setWindowTitle("Horiba Automate")
        self.setFixedSize(QSize(180, 280))

        self.layout = QVBoxLayout(self)

        # calling method 
        self.UiComponents(self.layout)
        self.mesaApp = mesa.mesa("COM4")

        

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
        if self.mesaApp.boot() == True:
            self.mesaApp.start()
        

    def clickStop(self):
        self.mesaApp.running = False
        sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()