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

from PyQt6.QtCore import QSize, Qt, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QLabel, QPushButton, QVBoxLayout, 
                              QHBoxLayout, QWidget, QMainWindow, QCheckBox, 
                              QMessageBox, QTextEdit, QScrollBar)
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtGui import QTextCursor, QFont

class MainWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.setWindowTitle("Horiba Automation System")
        self.setFixedSize(QSize(600, 500))

        self.layout = QVBoxLayout(self)

        # calling method 
        self.UiComponents(self.layout)
        self.mesaApp = mesa.mesa("COM4")
        
        # Connect error and success signals to log display (no popup dialogs)
        self.mesaApp.error_occurred.connect(self.log_error)
        self.mesaApp.process_completed.connect(self.log_success)
        self.mesaApp.status_update.connect(self.log_status)

        self.mesaApp.log_message.connect(self.log_message)  # Connect detailed logging

    # method for widgets 
    def UiComponents(self, layout): 
        
        # Label at the top, centered
        label = QLabel("<h2>Horiba Automation System</h2>")
        layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Status label
        self.statusLabel = QLabel("Status: Ready", self)
        self.statusLabel.setStyleSheet("QLabel { color: green; font-weight: bold; font-size: 14px; }")
        layout.addWidget(self.statusLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Horizontal layout for checkboxes (left) and buttons (right)
        horizontal_layout = QHBoxLayout()
        
        # Left side: Checkboxes in a vertical layout
        checkboxes_layout = QVBoxLayout()
        
        checkboxes_label = QLabel("<b>Select Processes:</b>")
        checkboxes_layout.addWidget(checkboxes_label)
        
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
        
        buttons_label = QLabel("<b>Control:</b>")
        buttons_layout.addWidget(buttons_label)
        
        self.btStart = QPushButton("Start", self) 
        self.btStop = QPushButton("Stop", self) 
        self.btClear = QPushButton("Clear Log", self)
  
        # setting size of button 
        self.btStart.setFixedSize(120, 40)
        self.btStop.setFixedSize(120, 40)
        self.btClear.setFixedSize(120, 40)
        
        # Style buttons
        self.btStart.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.btStop.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        self.btClear.setStyleSheet("QPushButton { background-color: #2196F3; color: white; font-weight: bold; }")
        
        buttons_layout.addWidget(self.btStart)
        buttons_layout.addWidget(self.btStop)
        buttons_layout.addWidget(self.btClear)
        buttons_layout.addStretch()  # Push buttons to top
        
        # Add left and right sections to horizontal layout
        horizontal_layout.addLayout(checkboxes_layout)
        horizontal_layout.addStretch()  # Space between checkboxes and buttons
        horizontal_layout.addLayout(buttons_layout)
        
        # Add horizontal layout to main layout
        layout.addLayout(horizontal_layout)
        
        # Add log text area
        log_label = QLabel("<b>Process Log:</b>")
        layout.addWidget(log_label)
        
        self.logTextEdit = QTextEdit(self)
        self.logTextEdit.setReadOnly(True)
        self.logTextEdit.setMinimumHeight(200)
        
        # Set font for better readability
        font = QFont("Consolas", 9)
        self.logTextEdit.setFont(font)
        
        # Dark theme for log
        self.logTextEdit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
            }
        """)
        
        layout.addWidget(self.logTextEdit)
  
        # adding action to buttons
        self.btStart.clicked.connect(self.clickStart) 
        self.btStop.clicked.connect(self.clickStop)
        self.btClear.clicked.connect(self.clickClear)
        
        # Initial log message
        self.log_message("System initialized. Ready to start.", "INFO")
  
    def log_message(self, message, level="INFO"):
        """Add a message to the log with timestamp and color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding based on level
        if level == "ERROR":
            color = "#ff6b6b"  # Red
            prefix = "❌"
        elif level == "SUCCESS":
            color = "#51cf66"  # Green
            prefix = "✓"
        elif level == "WARNING":
            color = "#ffd93d"  # Yellow
            prefix = "⚠"
        elif level == "INFO":
            color = "#74c0fc"  # Blue
            prefix = "ℹ"
        else:
            color = "#d4d4d4"  # Default
            prefix = "•"
        
        # Format message with HTML
        formatted_message = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{prefix} {level}:</span> <span style="color: {color};">{message}</span>'
        
        # Append to log
        self.logTextEdit.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.logTextEdit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
  
    # action method 
    def clickStart(self): 
        # Check if at least one checkbox is checked
        if not (self.checkbox1.isChecked() or self.checkbox2.isChecked() or 
                self.checkbox3.isChecked() or self.checkbox4.isChecked()):
            # Log warning instead of popup
            self.log_message("Please select at least one process before starting.", "WARNING")
            return
        
        # Disable start button to prevent multiple clicks
        self.btStart.setEnabled(False)
        
        # Update status
        self.statusLabel.setText("Status: Starting...")
        self.statusLabel.setStyleSheet("QLabel { color: orange; font-weight: bold; font-size: 14px; }")
        self.log_message("Starting Horiba Automation System...", "INFO")
        
        # Launch the MESA application
        try:
            self.log_message("Launching MESA application...", "INFO")
            os.chdir(r"C:\Program Files (x86)\HORIBA\HORIBA X-RAY LAB For MESA-50 SERIES")
            subprocess.Popen("MesaApplication.exe")
            os.chdir(r"D:\horiba-automation")
            self.log_message("MESA application launched successfully", "SUCCESS")
        except Exception as e:
            self.log_message(f"Failed to launch MESA application: {str(e)}", "ERROR")
            self.btStart.setEnabled(True)
            return
        
        # Boot the system
        self.log_message("Initiating boot sequence...", "INFO")
        self.mesaApp.do_warmup = self.checkbox1.isChecked()
        self.mesaApp.bootStatus = self.mesaApp.boot()
        
        if self.mesaApp.bootStatus:
            # Set process flags based on checkbox selections
            self.mesaApp.do_egat_cal = self.checkbox2.isChecked()
            self.mesaApp.do_egat_50kv = self.checkbox3.isChecked()
            self.mesaApp.do_egat_15kv = self.checkbox4.isChecked()
            
            # Log selected processes
            self.log_message("Boot successful. Selected processes:", "SUCCESS")
            if self.mesaApp.do_warmup:
                self.log_message("  ➤ Warmup", "INFO")
            if self.mesaApp.do_egat_cal:
                self.log_message("  ➤ EGAT Cal Curve", "INFO")
            if self.mesaApp.do_egat_50kv:
                self.log_message("  ➤ EGAT 50kV", "INFO")
            if self.mesaApp.do_egat_15kv:
                self.log_message("  ➤ EGAT 15kV", "INFO")
            
            # Update status
            self.statusLabel.setText("Status: Running")
            self.statusLabel.setStyleSheet("QLabel { color: green; font-weight: bold; font-size: 14px; }")

            self.mesaApp.running = True
            
            # Start the thread
            self.mesaApp.start()
            self.log_message("Automation started. Waiting for serial trigger (MESA,MSS)...", "INFO")
            
        else: 
            self.mesaApp.data_send.emit("MESA,E01\n")
            self.statusLabel.setText("Status: Boot Failed")
            self.statusLabel.setStyleSheet("QLabel { color: red; font-weight: bold; font-size: 14px; }")
            self.log_message("Boot sequence failed. Please check connections.", "ERROR")
            self.btStart.setEnabled(True)

    def clickStop(self):
        """Stop the running processes and close the application"""
        self.log_message("Stop button pressed. Shutting down...", "WARNING")
        self.mesaApp.running = False
        
        # Wait a bit for the thread to finish
        if self.mesaApp.isRunning():
            self.log_message("Waiting for processes to complete...", "INFO")
            self.mesaApp.wait(2000)  # Wait up to 2 seconds
        
        self.log_message("System shutdown complete.", "INFO")
        sys.exit()
    
    def clickClear(self):
        """Clear the log text area"""
        self.logTextEdit.clear()
        self.log_message("Log cleared.", "INFO")
    
    def log_error(self, title, message):
        """Log error message (no popup dialog)"""
        self.log_message(f"{title}: {message}", "ERROR")
        # Update status to show error
        self.statusLabel.setText("Status: Error")
        self.statusLabel.setStyleSheet("QLabel { color: red; font-weight: bold; font-size: 14px; }")
    
    def log_success(self, message):
        """Log success message (no popup dialog)"""
        self.log_message(message, "SUCCESS")
    
    def log_status(self, status):
        """Update status label and log"""
        self.statusLabel.setText(status)
        
        # Extract just the status message (remove "Status: " prefix if present)
        display_message = status.replace("Status: ", "")
        
        # Determine log level and color based on status
        if "Failed" in status or "Error" in status:
            self.statusLabel.setStyleSheet("QLabel { color: red; font-weight: bold; font-size: 14px; }")
            self.log_message(display_message, "ERROR")
            # Re-enable start button on failure
            self.btStart.setEnabled(True)
        elif "Running" in status or "Waiting" in status:
            self.statusLabel.setStyleSheet("QLabel { color: orange; font-weight: bold; font-size: 14px; }")
            self.log_message(display_message, "INFO")
        elif "Completed" in status or "Success" in status:
            self.statusLabel.setStyleSheet("QLabel { color: green; font-weight: bold; font-size: 14px; }")
            self.log_message(display_message, "SUCCESS")
            # Re-enable start button on completion
            self.btStart.setEnabled(True)
        else:
            self.statusLabel.setStyleSheet("QLabel { color: blue; font-weight: bold; font-size: 14px; }")
            self.log_message(display_message, "INFO")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()