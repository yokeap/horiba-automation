import autoit
import pyautogui
import threading
from datetime import datetime
# from . import serial_port
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow

try:
    import Queue
except:
    import queue as Queue
import sys, time, serial

class serial_port(QObject):
    data_received = pyqtSignal(str)
    data_send = pyqtSignal(str)
    def __init__(self):
        QObject.__init__(self)
        self.serial_port = QSerialPort()
        self.serial_port.readyRead.connect(self.on_ready_read)

    def open_port(self, port_name):
        if self.serial_port.isOpen():
            self.serial_port.close()
        self.serial_port.setPortName(port_name)
        # self.serial_port.setBaudRate(9600)
        # self.serial_port.setDataBits(QSerialPort.DataBits.Data8)
        # self.serial_port.setParity(QSerialPort.Parity.NoParity)
        # self.serial_port.setStopBits(QSerialPort.StopBits.OneStop)
        # self.serial_port.open(QSerialPort.OpenModeFlag.ReadWrite)
        self.serial_port.setBaudRate(QSerialPort.Baud9600)
        self.serial_port.setDataBits(QSerialPort.Data8)
        self.serial_port.setParity(QSerialPort.NoParity)
        self.serial_port.setStopBits(QSerialPort.OneStop)
        self.serial_port.open(QSerialPort.ReadWrite)

    @pyqtSlot(str)
    def write_data(self, data):
        print(data)
        if self.serial_port.isOpen():
            self.serial_port.writeData(data.encode())

    @pyqtSlot()
    def on_ready_read(self):
        if self.serial_port.canReadLine():
            data = self.serial_port.readLine().data().decode().strip()
            self.data_received.emit(data)

class mesa(QThread):
    data_send = pyqtSignal(str)
    def __init__(self, comport):
        # QWidget.__init__(self)
        QThread.__init__(self)
        # super().__init__()
        # self.serial_port = QSerialPort()
        # self.serial_port.readyRead.connect(self.on_ready_read)
        # self.serial_port.open(comport)
        self.serial_port = serial_port()
        self.serial_port.open_port(comport)
        self.serial_port.data_received.connect(self.on_data_received)
        self.data_send.connect(self.serial_port.write_data)
        self.running = True
        self.serialReceive = 0
        self.init = False

        # self.stop_event = threading.Event()
        n=0
        # self.data_send.emit("MESA,CHK\n")
        # while n < 3:
        #     if self.serialReceive == "MESA,RDY":
        #         self.serialReceive = ""
        #         self.init = True
        #         n = 3
        #     time.sleep(1) 

        # self.mesaThread = threading.Thread(target=self.run)
        # self.mesaThread.daemon = True
        self.init = True
    
    # def open_port(self, port_name):
    #     if self.serial_port.isOpen():
    #         self.serial_port.close()
    #     self.serial_port.setPortName(port_name)
    #     # self.serial_port.setBaudRate(9600)
    #     # self.serial_port.setDataBits(QSerialPort.DataBits.Data8)
    #     # self.serial_port.setParity(QSerialPort.Parity.NoParity)
    #     # self.serial_port.setStopBits(QSerialPort.StopBits.OneStop)
    #     # self.serial_port.open(QSerialPort.OpenModeFlag.ReadWrite)
    #     self.serial_port.setBaudRate(QSerialPort.Baud9600)
    #     self.serial_port.setDataBits(QSerialPort.Data8)
    #     self.serial_port.setParity(QSerialPort.NoParity)
    #     self.serial_port.setStopBits(QSerialPort.OneStop)
    #     self.serial_port.open(QSerialPort.ReadWrite)

    # def write_data(self, data):
    #     if self.serial_port.isOpen():
    #         self.serial_port.writeData(data.encode())

    # def on_ready_read(self):
    #     if self.serial_port.canReadLine():
    #         data = self.serial_port.readLine().data().decode().strip()
    #         self.data_received.emit(data)

    def boot(self):
        # bootup process
        # self.data_send.emit("MESA,CHK\n")
        self.data_send.emit("MESA,CHK\n")
        time.sleep(10) 
        try:
            pyautogui.click('./imgdata/_0_btCancel.png')
        except pyautogui.ImageNotFoundException:
            print('Error: Start program')
            self.data_send.emit("MESA,ALM\n")
            return False

        ################ project open process ###################
        time.sleep(1)
        try:
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(1) 
            pyautogui.click('./imgdata/_1_ltProjectOpen.png', clicks=2)
        except pyautogui.ImageNotFoundException:
            print('Error: project open')
            self.data_send.emit("MESA,ALM\n")
            return False
        return True
        
    def process(self):
        
        ################# run egat cal curve ####################
        time.sleep(2) 
        try:
            pyautogui.click('./imgdata/_2_btEGATCal.png')       
            # runState = pyautogui.locateOnScreen('calc7key.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot run')
            self.data_send.emit("MESA,ALM\n")
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
            self.data_send.emit("MESA,ALM\n")
            return False


        ################## report process #######################
        time.sleep(1) 
        try:
            pyautogui.click('./imgdata/_3_btReport.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot report')
            self.data_send.emit("MESA,ALM\n")
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
            self.data_send.emit("MESA,ALM\n")
            return False

        except autoit.autoit.AutoItError as e:
            print(e)
            self.data_send.emit("MESA,ALM\n")
            return False

        ##################### close ############################
        time.sleep(1) 
        try:
            pyautogui.click('./imgdata/_6_btClose.png')
        except pyautogui.ImageNotFoundException:
            print('Error: cannot report')
            self.data_send.emit("MESA,ALM\n")
            return False  

   
    def run(self):
        # self.process.status = False
        # while not self.stop_event.is_set():
        #     if self.serialReceive == "MESA,SR":
        #         self.serialReceive = ""
        #         self.data_send.emit("MESA,MSR\n")
        #         self.process.status = self.process()
        #         if self.process() == False:
        #             self.stop_event.set()
        #             print("Thread stop!") 
        #             return False
        #         self.data_send.emit("MESA,MSD\n")
        while self.running:
            if self.serialReceive == "MESA,MS":
                    self.serialReceive = ""
                    # self.data_send.emit("MESA,MSR\n")
                    self.data_send.emit("MESA,MSR\n")
                    if self.process() == False:
                            self.running = False
                            print("Thread stop!") 
                            return False
                    self.data_send.emit("MESA,MSD\n")


    # def start_thread(self):        
    #     self.mesaThread.start()

    # def stop_thread(self):
    #     self.stop_event.set()

    @pyqtSlot(str)
    def on_data_received(self, data):
        self.serialReceive = data
        print(self.serialReceive)

    # @pyqtSlot()
    # def push_data(self, data):
    #     self.serial_port.data_send.emit(data)
