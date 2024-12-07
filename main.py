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

from PyQt6.QtCore import QSize, Qt, pyqtSlot, QObject, pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo

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
        # os.chdir(r"C:\Program Files (x86)\HORIBA\HORIBA X-RAY LAB For MESA-50 SERIES")
        subprocess.Popen("MesaApplication.exe")
        # os.chdir(r"D:\software\horiba-automation")
        self.mesaApp.bootStatus = self.mesaApp.boot()
        if self.mesaApp.bootStatus == True:
            # self.mesaApp.data_send.emit("MESA,CHK\n")
            self.mesaApp.start()
        else: 
            self.mesaApp.data_send.emit("MESA,ALM\n")
        # if self.mesaApp.boot() == True:
        #     self.mesaApp.start()
        

    def clickStop(self):
        self.mesaApp.running = False
        sys.exit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()