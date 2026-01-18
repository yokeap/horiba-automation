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
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QWidget, QMainWindow, QCheckBox, QMessageBox
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo

class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.setWindowTitle("Horiba Automate")
        self.setFixedSize(QSize(280, 230))

        self.layout = QVBoxLayout(self)

        # calling method 
        self.UiComponents(self.layout)
        self.mesaApp = mesa.mesa("COM4")
        
        # Connect error and success signals to show message boxes
        self.mesaApp.error_occurred.connect(self.show_error_message)
        self.mesaApp.process_completed.connect(self.show_success_message)
        self.mesaApp.status_update.connect(self.update_status)

    # method for widgets 
    def UiComponents(self, layout): 
        
        # Label at the top, centered
        label = QLabel("<h1>Horiba Automation</h1>")
        label1 = QLabel("<h1>System</h1>")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label1, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.statusLabel = QLabel("Status: Ready to Run", self)
        self.statusLabel.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        layout.addWidget(self.statusLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Horizontal layout for checkboxes (left) and buttons (right)
        horizontal_layout = QHBoxLayout()
        
        # Left side: Checkboxes in a vertical layout
        checkboxes_layout = QVBoxLayout()
        self.checkbox1 = QCheckBox("Warmup", self)
        self.checkbox2 = QCheckBox("EGAT Cal Curve", self)
        self.checkbox3 = QCheckBox("EGAT 50kV", self)
        self.checkbox4 = QCheckBox("EGAT 15kV", self)
        
        checkboxes_layout.addWidget(self.checkbox1)
        checkboxes_layout.addWidget(self.checkbox2)
        checkboxes_layout.addWidget(self.checkbox3)
        checkboxes_layout.addWidget(self.checkbox4)
        checkboxes_layout.addStretch()  # Push checkboxes to top
        
        # Right side: Buttons in a vertical layout
        buttons_layout = QVBoxLayout()
        btStart = QPushButton("Start", self) 
        btStop = QPushButton("Stop", self) 
  
        # setting size of button 
        btStart.setFixedSize(100, 50)
        btStop.setFixedSize(100, 50)
        
        buttons_layout.addWidget(btStart)
        buttons_layout.addWidget(btStop)
        buttons_layout.addStretch()  # Push buttons to top
        
        # Add left and right sections to horizontal layout
        horizontal_layout.addLayout(checkboxes_layout)
        horizontal_layout.addStretch()  # Space between checkboxes and buttons
        horizontal_layout.addLayout(buttons_layout)
        
        # Add horizontal layout to main layout
        layout.addLayout(horizontal_layout)
  
        # adding action to a button 
        btStart.clicked.connect(self.clickStart) 
        btStop.clicked.connect(self.clickStop) 
  
  
    # action method 
    def clickStart(self): 
        # Check if at least one checkbox is checked
        if not (self.checkbox1.isChecked() or self.checkbox2.isChecked() or 
                self.checkbox3.isChecked() or self.checkbox4.isChecked()):
            # Show warning dialog if no checkbox is checked
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Warning")
            msg.setText("Please select at least one option before starting.")
            msg.exec()
            return
        
        # Update status
        self.statusLabel.setText("Status: Booting...")
        self.statusLabel.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
        
        # Launch the MESA application
        subprocess.Popen("MesaApplication.exe")
        
        # Boot the system
        self.mesaApp.do_warmup = self.checkbox1.isChecked()
        self.mesaApp.bootStatus = self.mesaApp.boot()
        
        if self.mesaApp.bootStatus:
            # Set process flags based on checkbox selections
            self.mesaApp.do_egat_cal = self.checkbox2.isChecked()
            self.mesaApp.do_egat_50kv = self.checkbox3.isChecked()
            self.mesaApp.do_egat_15kv = self.checkbox4.isChecked()
            
            # Print selected processes for debugging
            print("Selected processes:")
            if self.mesaApp.do_warmup:
                print("  - Warmup")
            if self.mesaApp.do_egat_cal:
                print("  - EGAT Cal Curve")
            if self.mesaApp.do_egat_15kv:
                print("  - EGAT 15kV")
            if self.mesaApp.do_egat_50kv:
                print("  - EGAT 50kV")
            
            # Update status
            self.statusLabel.setText("Status: Ready to Run")
            self.statusLabel.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            # Start the thread
            self.mesaApp.start()
            
        else: 
            self.mesaApp.data_send.emit("MESA,E01\n")
            self.statusLabel.setText("Status: Boot Failed")
            self.statusLabel.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def clickStop(self):
        """Stop the running processes and close the application"""
        self.mesaApp.running = False
        # Wait a bit for the thread to finish
        if self.mesaApp.isRunning():
            self.mesaApp.wait(2000)  # Wait up to 2 seconds
        sys.exit()
    
    def show_error_message(self, title, message):
        """Show error message box"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def show_success_message(self, message):
        """Show success message box"""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("Success")
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()
    
    def update_status(self, status):
        """Update status label"""
        self.statusLabel.setText(status)
        if "Failed" in status or "Error" in status:
            self.statusLabel.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        elif "Running" in status or "Waiting" in status:
            self.statusLabel.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
        elif "Completed" in status or "Success" in status:
            self.statusLabel.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.statusLabel.setStyleSheet("QLabel { color: blue; font-weight: bold; }")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()