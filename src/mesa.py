import autoit
import pyautogui
import threading
from datetime import datetime
import os
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow

try:
    import Queue
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    import queue as Queue
    OPENCV_AVAILABLE = False
    print("Warning: OpenCV (cv2) not installed. Image detection will use basic matching without confidence levels.")
    print("To install: pip install opencv-python")
    
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
        self.serial_port.setBaudRate(9600)
        self.serial_port.setDataBits(QSerialPort.DataBits.Data8)
        self.serial_port.setParity(QSerialPort.Parity.NoParity)
        self.serial_port.setStopBits(QSerialPort.StopBits.OneStop)
        self.serial_port.open(QSerialPort.OpenModeFlag.ReadWrite)

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
    error_occurred = pyqtSignal(str, str)
    process_completed = pyqtSignal(str)
    status_update = pyqtSignal(str)
    log_message = pyqtSignal(str, str)  # NEW: Signal for detailed logging
    
    def __init__(self, comport):
        QThread.__init__(self)
        self.serial_port = serial_port()
        self.serial_port.open_port(comport)
        self.serial_port.data_received.connect(self.on_data_received)
        self.data_send.connect(self.serial_port.write_data)
        self.running = True
        self.serialReceive = 0
        self.bootStatus = False
        self.init = True
        
        # Process flags from checkboxes
        self.do_warmup = False
        self.do_egat_cal = False
        self.do_egat_15kv = False
        self.do_egat_50kv = False
        
        # Configure pyautogui settings for better reliability
        pyautogui.PAUSE = 0.5
        pyautogui.FAILSAFE = True

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    def log(self, message, level="INFO"):
        """Helper method to emit log messages to GUI"""
        print(message)
        self.log_message.emit(message, level)

    def find_and_click(self, image_path, confidence=0.8, retries=3, timeout=5, click_count=1):
        """Improved image detection and clicking"""
        start_time = time.time()
        attempt = 0
        
        while attempt < retries and (time.time() - start_time) < timeout:
            try:
                confidence_levels = [confidence, confidence - 0.1, confidence - 0.2]
                
                for conf in confidence_levels:
                    if conf < 0.5:
                        continue
                    
                    location = pyautogui.locateOnScreen(image_path, confidence=conf)
                    
                    if location:
                        center = pyautogui.center(location)
                        self.log(f"Found image: {image_path} at {center} with confidence {conf}", "INFO")
                        
                        pyautogui.click(center.x, center.y, clicks=click_count)
                        time.sleep(0.5)
                        return True
                
                self.log(f"Attempt {attempt + 1}/{retries}: Image not found: {image_path}", "INFO")
                time.sleep(1)
                attempt += 1
                
            except pyautogui.ImageNotFoundException:
                self.log(f"Attempt {attempt + 1}/{retries}: Image not found exception: {image_path}", "INFO")
                time.sleep(1)
                attempt += 1
            except Exception as e:
                error_msg = f"Error in find_and_click: {e}"
                self.log(error_msg, "ERROR")
                time.sleep(1)
                attempt += 1
        
        error_msg = f"Failed to find image after {retries} attempts: {os.path.basename(image_path)}"
        self.log(error_msg, "ERROR")
        return False

    def wait_for_image(self, image_path, confidence=0.8, timeout=300, check_interval=5):
        """Wait for an image to appear on screen"""
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                confidence_levels = [confidence, confidence - 0.1, confidence - 0.2]
                
                for conf in confidence_levels:
                    if conf < 0.5:
                        continue
                    
                    location = pyautogui.locateOnScreen(image_path, confidence=conf)
                    if location:
                        self.log(f"Image appeared: {image_path} with confidence {conf}", "INFO")
                        return True
                
                elapsed = time.time() - start_time
                self.log(f"Waiting for image: {image_path} ({elapsed:.1f}/{timeout}s)", "INFO")
                time.sleep(check_interval)
                
            except pyautogui.ImageNotFoundException:
                time.sleep(check_interval)
            except Exception as e:
                self.log(f"Error waiting for image: {e}", "ERROR")
                time.sleep(check_interval)
        
        self.log(f"Timeout waiting for image: {image_path}", "ERROR")
        return False

    def boot(self):
        """Bootup process with improved image detection"""
        self.log("Starting boot process...", "INFO")
        time.sleep(10)

        self.log("Looking for calibration window...", "INFO")
        if not self.find_and_click('./imgdata/bt_cal_energy_copy.png', confidence=0.7, retries=3):
            self.log('Warning: Calibration window not found, continuing...', "WARNING")
        
        time.sleep(1)
        self.log("Looking for cancel button...", "INFO")
        if not self.find_and_click('./imgdata/_0_btCancel.png', confidence=0.8, retries=3):
            self.error_occurred.emit("Boot Error", "Cannot find cancel button. Please ensure the application is running.")
            return False

        time.sleep(1)
        self.log("Opening project...", "INFO")
        try:
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(2)
            
            if not self.find_and_click('./imgdata/_1_ltProjectOpen.png', confidence=0.95, retries=3, click_count=2):
                self.error_occurred.emit("Boot Error", "Cannot find project to open. Please check if the project list is visible.")
                return False
                
        except Exception as e:
            error_msg = f'Error in project open: {str(e)}'
            self.log(error_msg, "ERROR")
            self.error_occurred.emit("Boot Error", error_msg)
            return False
        
        if self.do_warmup:
            self.log("\n========== Executing Warmup ==========", "INFO")
            self.status_update.emit("Running Warmup...")
            if not self.warmupProcess():
                self.error_occurred.emit("Boot Error", "Warmup failed - stopping thread.")
                self.status_update.emit("Status: Failed")
                self.log("Warmup failed - stopping thread", "ERROR")
                return False
            
        self.data_send.emit("MESA,CHK\n")
        self.log("Boot process completed successfully", "SUCCESS")
        return True
    
    def warmupProcess(self):
        """Warmup process implementation with improved detection"""
        self.log("Starting Warmup process...", "INFO")
        time.sleep(2)
        
        if not self.find_and_click('./imgdata/bt_warmup.png', confidence=0.8, retries=5):
            self.log('Error: Cannot start warmup process', "ERROR")
            self.error_occurred.emit("Warmup Error", "Cannot start warmup process. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log("Waiting for warmup to complete...", "INFO")
        time.sleep(60)
        
        self.log("Warmup process completed", "SUCCESS")
        self.process_completed.emit("Warmup process completed successfully")
        return True
    
    def egat15kVProcess(self):
        """EGAT 15kV process implementation"""
        self.log("Starting EGAT 15kV process...", "INFO")
        time.sleep(2)
        
        if not self.find_and_click('./imgdata/bt_egat_15kv.png', confidence=0.8, retries=5):
            self.log('Error: Cannot start EGAT 15kV process', "ERROR")
            self.error_occurred.emit("EGAT 15kV Error", "Cannot start EGAT 15kV process. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log("Waiting for EGAT 15kV process to complete...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=5):
            self.log("EGAT 15kV process timeout or incomplete", "ERROR")
            self.error_occurred.emit("EGAT 15kV Error", "Process timeout or incomplete. Ready signal not detected.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        if self.saveReport("EGAT-15kV"):
            self.process_completed.emit("EGAT 15kV process completed successfully")
            return True
        return False
    
    def egat50kVProcess(self):
        """EGAT 50kV process implementation"""
        self.log("Starting EGAT 50kV process...", "INFO")
        time.sleep(2)
        
        if not self.find_and_click('./imgdata/bt_egat_50kv.png', confidence=0.8, retries=5):
            self.log('Error: Cannot start EGAT 50kV process', "ERROR")
            self.error_occurred.emit("EGAT 50kV Error", "Cannot start EGAT 50kV process. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log("Waiting for EGAT 50kV process to complete...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=5):
            self.log("EGAT 50kV process timeout or incomplete", "ERROR")
            self.error_occurred.emit("EGAT 50kV Error", "Process timeout or incomplete. Ready signal not detected.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        if self.saveReport("EGAT-50kV"):
            self.process_completed.emit("EGAT 50kV process completed successfully")
            return True
        return False
        
    def egatCalCurveProcess(self):
        """EGAT Calibration Curve process implementation"""
        self.log("Starting EGAT Cal Curve process...", "INFO")
        time.sleep(2)
        
        if not self.find_and_click('./imgdata/_2_btEGATCal.png', confidence=0.8, retries=5):
            self.log('Error: Cannot run EGAT Cal Curve', "ERROR")
            self.error_occurred.emit("EGAT Cal Curve Error", "Cannot run EGAT Cal Curve. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False

        self.log("Waiting for EGAT Cal Curve process to complete...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=10):
            self.log("EGAT Cal Curve process incomplete", "ERROR")
            self.error_occurred.emit("EGAT Cal Curve Error", "Process timeout or incomplete. Ready signal not detected.")
            self.data_send.emit("MESA,ALM\n")
            return False

        if self.saveReport("EGAT-CAL"):
            self.process_completed.emit("EGAT Cal Curve process completed successfully")
            return True
        return False
    
    def saveReport(self, process_name):
        """Common report saving function"""
        self.log(f"Saving report for {process_name}...", "INFO")
        
        time.sleep(1)
        if not self.find_and_click('./imgdata/_3_btReport.png', confidence=0.8, retries=5):
            self.log('Error: Cannot open report', "ERROR")
            self.error_occurred.emit("Report Error", f"Cannot open report for {process_name}. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False

        time.sleep(3)
        try:
            if not self.find_and_click('./imgdata/_4_btExport.png', confidence=0.8, retries=5):
                self.log('Error: Cannot click export button', "ERROR")
                self.error_occurred.emit("Export Error", f"Cannot click export button for {process_name}.")
                self.data_send.emit("MESA,ALM\n")
                return False
            
            time.sleep(1)
            
            if not self.find_and_click('./imgdata/_5_ddExcel.png', confidence=0.8, retries=5):
                self.log('Error: Cannot select Excel format', "ERROR")
                self.error_occurred.emit("Export Error", f"Cannot select Excel format for {process_name}.")
                self.data_send.emit("MESA,ALM\n")
                return False
            
            if not autoit.win_wait_active("Save As", 10):
                self.log('Error: Save As dialog did not appear', "ERROR")
                self.error_occurred.emit("Save Error", f"Save As dialog did not appear for {process_name}.")
                self.data_send.emit("MESA,ALM\n")
                return False
            
            time.sleep(1)
            saveDT = "Report_" + process_name + "_" + datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
            autoit.control_send("Save As", "Edit1", saveDT)
            time.sleep(1)
            autoit.control_click("Save As", "Button2")
            
        except pyautogui.ImageNotFoundException as e:
            self.log(f'PyAutoGUI error in save process: {e}', "ERROR")
            self.error_occurred.emit("Save Error", f'PyAutoGUI error in save process for {process_name}: {str(e)}')
            self.data_send.emit("MESA,ALM\n")
            return False
        except autoit.autoit.AutoItError as e:
            self.log(f'AutoIt error in save process: {e}', "ERROR")
            self.error_occurred.emit("Save Error", f'AutoIt error in save process for {process_name}: {str(e)}')
            self.data_send.emit("MESA,ALM\n")
            return False
        except Exception as e:
            self.log(f'Unexpected error in save process: {e}', "ERROR")
            self.error_occurred.emit("Save Error", f'Unexpected error in save process for {process_name}: {str(e)}')
            self.data_send.emit("MESA,ALM\n")
            return False

        time.sleep(2)
        if not self.find_and_click('./imgdata/_6_btClose.png', confidence=0.8, retries=5):
            self.log('Error: Cannot close report window', "ERROR")
            self.error_occurred.emit("Close Error", f"Cannot close report window for {process_name}.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log(f"{process_name} report saved successfully", "SUCCESS")
        return True

    def run(self):
        """Main thread execution - runs selected processes in sequence"""
        while self.running:
            if self.serialReceive == "MESA,MSS":
                self.serialReceive = ""
                self.data_send.emit("MESA,MSR\n")
                
                all_success = True
                
                if self.do_egat_cal and all_success:
                    self.log("\n========== Executing EGAT Cal Curve ==========", "INFO")
                    if not self.egatCalCurveProcess():
                        all_success = False
                        self.running = False
                        self.log("EGAT Cal Curve failed - stopping thread", "ERROR")
                        break
                
                if self.do_egat_50kv and all_success:
                    self.log("\n========== Executing EGAT 50kV ==========", "INFO")
                    if not self.egat50kVProcess():
                        all_success = False
                        self.running = False
                        self.log("EGAT 50kV failed - stopping thread", "ERROR")
                        break
                
                if self.do_egat_15kv and all_success:
                    self.log("\n========== Executing EGAT 15kV ==========", "INFO")
                    if not self.egat15kVProcess():
                        all_success = False
                        self.running = False
                        self.log("EGAT 15kV failed - stopping thread", "ERROR")
                        break
                
                if all_success:
                    self.data_send.emit("MESA,MSD\n")
                    self.status_update.emit("Status: All Completed Successfully")
                    self.log("\n========== All selected processes completed successfully ==========", "SUCCESS")
                else:
                    return False
                    
            else:
                self.serialReceive = ""
            
            time.sleep(0.1)

    @pyqtSlot(str)
    def on_data_received(self, data):
        self.serialReceive = data
        self.log(f"Serial received: {self.serialReceive}", "INFO")