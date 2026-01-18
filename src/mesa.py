import autoit
import pyautogui
import threading
from datetime import datetime
import os
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QThread
from PyQt6.QtSerialPort import QSerialPort, QSerialPortInfo
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget, QMainWindow

# FIXED: Separate try blocks for Queue and cv2
try:
    import Queue
except ImportError:
    import queue as Queue

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    
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
        if self.serial_port.isOpen():
            self.serial_port.writeData(data.encode())

    @pyqtSlot()
    def on_ready_read(self):
        if self.serial_port.canReadLine():
            data = self.serial_port.readLine().data().decode().strip()
            self.data_received.emit(data)

class mesa(QThread):
    data_send = pyqtSignal(str)
    error_occurred = pyqtSignal(str, str)  # Signal for error messages (title, message)
    process_completed = pyqtSignal(str)  # Signal for success messages
    status_update = pyqtSignal(str)  # Signal for status updates
    log_message = pyqtSignal(str, str)  # NEW: Signal for detailed logging (message, level)
    
    def __init__(self, comport):
        QThread.__init__(self)
        self.serial_port = serial_port()
        self.serial_port.open_port(comport)
        self.serial_port.data_received.connect(self.on_data_received)
        self.data_send.connect(self.serial_port.write_data)
        self.running = True
        self.serialReceive = ""  # FIXED: Changed from 0 to "" (string)
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
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)
    
    def log(self, message, level="INFO"):
        """Helper method to emit log messages to GUI"""
        print(message)  # Still print to console for debugging
        self.log_message.emit(message, level)

    def find_and_click(self, image_path, confidence=0.8, retries=3, timeout=10, click_count=1):
        """Improved image detection and clicking with comprehensive logging"""
        # Use resource_path for PyInstaller
        if not os.path.isabs(image_path):
            image_path = self.resource_path(image_path)
        
        image_name = os.path.basename(image_path)
        self.log(f"Searching for image: {image_name}", "INFO")
        
        start_time = time.time()
        attempt = 0
        
        while attempt < retries and (time.time() - start_time) < timeout:
            try:
                if OPENCV_AVAILABLE:
                    # Try different confidence levels with OpenCV
                    confidence_levels = [confidence, max(0.5, confidence - 0.1), max(0.5, confidence - 0.2)]
                    
                    for conf in confidence_levels:
                        location = pyautogui.locateOnScreen(image_path, confidence=conf, grayscale=True)
                        
                        if location:
                            center = pyautogui.center(location)
                            self.log(f"✓ Found {image_name} at ({center.x}, {center.y}) with confidence {conf:.2f}", "SUCCESS")
                            
                            # Click on the center
                            pyautogui.click(center.x, center.y, clicks=click_count)
                            click_type = "double-clicked" if click_count == 2 else "clicked"
                            self.log(f"✓ {click_type.capitalize()} {image_name}", "SUCCESS")
                            time.sleep(0.5)
                            return True
                else:
                    # Fallback: basic matching without confidence
                    location = pyautogui.locateOnScreen(image_path)
                    
                    if location:
                        center = pyautogui.center(location)
                        self.log(f"✓ Found {image_name} at ({center.x}, {center.y})", "SUCCESS")
                        
                        pyautogui.click(center.x, center.y, clicks=click_count)
                        click_type = "double-clicked" if click_count == 2 else "clicked"
                        self.log(f"✓ {click_type.capitalize()} {image_name}", "SUCCESS")
                        time.sleep(0.5)
                        return True
                
                # If not found, wait and retry
                self.log(f"Attempt {attempt + 1}/{retries}: Image not found, retrying...", "WARNING")
                time.sleep(1)
                attempt += 1
                
            except pyautogui.ImageNotFoundException:
                self.log(f"Attempt {attempt + 1}/{retries}: Image not detected", "WARNING")
                time.sleep(1)
                attempt += 1
            except Exception as e:
                error_msg = f"Error during image detection: {str(e)}"
                self.log(error_msg, "ERROR")
                self.error_occurred.emit("Detection Error", error_msg)
                time.sleep(1)
                attempt += 1
        
        error_msg = f"✗ Failed to find {image_name} after {retries} attempts"
        self.log(error_msg, "ERROR")
        self.error_occurred.emit("Image Not Found", error_msg)
        return False

    def wait_for_image(self, image_path, confidence=0.8, timeout=300, check_interval=5):
        """Wait for an image to appear with detailed logging"""
        if not os.path.isabs(image_path):
            image_path = self.resource_path(image_path)
        
        image_name = os.path.basename(image_path)
        self.log(f"Waiting for completion indicator: {image_name}", "INFO")
        self.log(f"Timeout: {timeout}s, checking every {check_interval}s", "INFO")
        
        start_time = time.time()
        last_log_time = start_time
        
        while (time.time() - start_time) < timeout:
            try:
                if OPENCV_AVAILABLE:
                    confidence_levels = [confidence, max(0.5, confidence - 0.1), max(0.5, confidence - 0.2)]
                    
                    for conf in confidence_levels:
                        location = pyautogui.locateOnScreen(image_path, confidence=conf, grayscale=True)
                        if location:
                            elapsed = time.time() - start_time
                            self.log(f"✓ Process completed! Ready signal detected after {elapsed:.1f}s", "SUCCESS")
                            return True
                else:
                    location = pyautogui.locateOnScreen(image_path)
                    if location:
                        elapsed = time.time() - start_time
                        self.log(f"✓ Process completed! Ready signal detected after {elapsed:.1f}s", "SUCCESS")
                        return True
                
                # Log progress every 15 seconds
                elapsed = time.time() - start_time
                if elapsed - last_log_time >= 15:
                    self.log(f"Still waiting... ({int(elapsed)}s / {timeout}s elapsed)", "INFO")
                    last_log_time = elapsed
                
                time.sleep(check_interval)
                
            except pyautogui.ImageNotFoundException:
                time.sleep(check_interval)
            except Exception as e:
                self.log(f"Error while waiting: {str(e)}", "ERROR")
                time.sleep(check_interval)
        
        self.log(f"✗ Timeout: Process did not complete within {timeout}s", "ERROR")
        return False

    def boot(self):
        """Bootup process with detailed logging"""
        self.log("=" * 50, "INFO")
        self.log("STARTING BOOT SEQUENCE", "INFO")
        self.log("=" * 50, "INFO")
        
        self.status_update.emit("Status: Boot - Initializing...")
        self.log("Waiting 10 seconds for MESA application to start...", "INFO")
        time.sleep(10)

        ################ skip calibration window ################### 
        self.log("Step 1: Checking for calibration window...", "INFO")
        self.status_update.emit("Status: Boot - Checking calibration...")
        
        if not self.find_and_click('./imgdata/bt_cal_energy_copy.png', confidence=0.7, retries=3):
            self.log("⚠ Calibration window not found (may be optional), continuing...", "WARNING")
        
        ################ skip cancel button ###################
        time.sleep(1)
        self.log("Step 2: Looking for cancel button...", "INFO")
        self.status_update.emit("Status: Boot - Finding cancel button...")
        
        if not self.find_and_click('./imgdata/_0_btCancel.png', confidence=0.8, retries=3):
            self.error_occurred.emit("Boot Error", "Cannot find cancel button")
            self.log("✗ Boot failed: Cancel button not found", "ERROR")
            return False

        ################ project open process ###################
        time.sleep(1)
        self.log("Step 3: Opening project...", "INFO")
        self.status_update.emit("Status: Boot - Opening project...")
        
        try:
            self.log("Sending Ctrl+O to open project dialog...", "INFO")
            pyautogui.hotkey('ctrl', 'o')
            time.sleep(2)
            
            self.log("Looking for project in list...", "INFO")
            if not self.find_and_click('./imgdata/_1_ltProjectOpen.png', confidence=0.8, retries=3, click_count=2):
                self.error_occurred.emit("Boot Error", "Cannot find project to open")
                self.log("✗ Boot failed: Project not found in list", "ERROR")
                return False
                
        except Exception as e:
            error_msg = f'Error opening project: {str(e)}'
            self.log(error_msg, "ERROR")
            self.error_occurred.emit("Boot Error", error_msg)
            return False
        
        ################ warmup if selected ###################
        if self.do_warmup:
            self.log("=" * 50, "INFO")
            self.log("EXECUTING WARMUP PROCESS", "INFO")
            self.log("=" * 50, "INFO")
            self.status_update.emit("Status: Running Warmup...")
            
            if not self.warmupProcess():
                self.error_occurred.emit("Warmup Error", "Warmup process failed")
                self.log("✗ Warmup failed", "ERROR")
                return False
            
        self.data_send.emit("MESA,CHK\n")
        self.log("✓ Boot sequence completed successfully", "SUCCESS")
        self.log("=" * 50, "INFO")
        self.status_update.emit("Status: Boot Complete - Ready")
        return True
    
    def warmupProcess(self):
        """Warmup process with detailed logging"""
        self.log("Looking for warmup button...", "INFO")
        time.sleep(2)
        
        if not self.find_and_click('./imgdata/bt_warmup.png', confidence=0.8, retries=5):
            self.error_occurred.emit("Warmup Error", "Warmup button not found")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log("Warmup started, waiting 60 seconds...", "INFO")
        self.status_update.emit("Status: Warmup in progress (60s)...")
        
        # Countdown logging
        for remaining in [45, 30, 15, 5]:
            time.sleep(15 if remaining == 45 else (15 if remaining > 15 else 10))
            if remaining > 0:
                self.log(f"Warmup: {remaining}s remaining...", "INFO")
        
        time.sleep(5)  # Final 5 seconds
        
        self.log("✓ Warmup process completed", "SUCCESS")
        self.process_completed.emit("Warmup process completed successfully")
        return True
    
    def egat15kVProcess(self):
        """EGAT 15kV process with detailed logging"""
        self.log("=" * 50, "INFO")
        self.log("STARTING EGAT 15kV PROCESS", "INFO")
        self.log("=" * 50, "INFO")
        
        self.status_update.emit("Status: Running EGAT 15kV...")
        time.sleep(2)
        
        self.log("Looking for EGAT 15kV button...", "INFO")
        if not self.find_and_click('./imgdata/bt_egat_15kv.png', confidence=0.8, retries=5):
            self.error_occurred.emit("EGAT 15kV Error", "Button not found")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log("EGAT 15kV process started, waiting for completion...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=5):
            self.error_occurred.emit("EGAT 15kV Error", "Process timeout")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        if self.saveReport("EGAT-15kV"):
            self.log("✓ EGAT 15kV process completed successfully", "SUCCESS")
            self.log("=" * 50, "INFO")
            self.process_completed.emit("EGAT 15kV process completed")
            return True
        return False
    
    def egat50kVProcess(self):
        """EGAT 50kV process with detailed logging"""
        self.log("=" * 50, "INFO")
        self.log("STARTING EGAT 50kV PROCESS", "INFO")
        self.log("=" * 50, "INFO")
        
        self.status_update.emit("Status: Running EGAT 50kV...")
        time.sleep(2)
        
        self.log("Looking for EGAT 50kV button...", "INFO")
        if not self.find_and_click('./imgdata/bt_egat_50kv.png', confidence=0.8, retries=5):
            self.error_occurred.emit("EGAT 50kV Error", "Button not found")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log("EGAT 50kV process started, waiting for completion...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=5):
            self.error_occurred.emit("EGAT 50kV Error", "Process timeout")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        if self.saveReport("EGAT-50kV"):
            self.log("✓ EGAT 50kV process completed successfully", "SUCCESS")
            self.log("=" * 50, "INFO")
            self.process_completed.emit("EGAT 50kV process completed")
            return True
        return False
        
    def egatCalCurveProcess(self):
        """EGAT Cal Curve process with detailed logging"""
        self.log("=" * 50, "INFO")
        self.log("STARTING EGAT CALIBRATION CURVE PROCESS", "INFO")
        self.log("=" * 50, "INFO")
        
        self.status_update.emit("Status: Running EGAT Cal Curve...")
        time.sleep(2)
        
        self.log("Looking for EGAT Cal Curve button...", "INFO")
        if not self.find_and_click('./imgdata/_2_btEGATCal.png', confidence=0.8, retries=5):
            self.error_occurred.emit("EGAT Cal Curve Error", "Button not found")
            self.data_send.emit("MESA,ALM\n")
            return False

        self.log("EGAT Cal Curve process started, waiting for completion...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=10):
            self.error_occurred.emit("EGAT Cal Curve Error", "Process timeout")
            self.data_send.emit("MESA,ALM\n")
            return False

        if self.saveReport("EGAT-CAL"):
            self.log("✓ EGAT Cal Curve process completed successfully", "SUCCESS")
            self.log("=" * 50, "INFO")
            self.process_completed.emit("EGAT Cal Curve process completed")
            return True
        return False
    
    def saveReport(self, process_name):
        """Save report with detailed logging"""
        self.log(f"Initiating report save for {process_name}...", "INFO")
        self.status_update.emit(f"Status: Saving {process_name} report...")
        
        ################## report process #######################
        time.sleep(1)
        self.log("Step 1: Opening report window...", "INFO")
        if not self.find_and_click('./imgdata/_3_btReport.png', confidence=0.8, retries=5):
            self.error_occurred.emit("Report Error", "Report button not found")
            self.data_send.emit("MESA,ALM\n")
            return False

        ################## export process #########################
        time.sleep(3)
        self.log("Step 2: Clicking export button...", "INFO")
        if not self.find_and_click('./imgdata/_4_btExport.png', confidence=0.8, retries=5):
            self.error_occurred.emit("Export Error", "Export button not found")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        time.sleep(1)
        self.log("Step 3: Selecting Excel format...", "INFO")
        if not self.find_and_click('./imgdata/_5_ddExcel.png', confidence=0.8, retries=5):
            self.error_occurred.emit("Export Error", "Excel format not found")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        ################## save dialog #########################
        self.log("Step 4: Waiting for Save As dialog...", "INFO")
        if not autoit.win_wait_active("Save As", 10):
            self.error_occurred.emit("Save Error", "Save As dialog did not appear")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        time.sleep(1)
        saveDT = "Report_" + process_name + "_" + datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
        self.log(f"Step 5: Entering filename: {saveDT}", "INFO")
        
        try:
            autoit.control_send("Save As", "Edit1", saveDT)
            time.sleep(1)
            
            self.log("Step 6: Clicking Save button...", "INFO")
            autoit.control_click("Save As", "Button2")
            
        except Exception as e:
            error_msg = f'Error saving file: {str(e)}'
            self.log(error_msg, "ERROR")
            self.error_occurred.emit("Save Error", error_msg)
            self.data_send.emit("MESA,ALM\n")
            return False

        ##################### close report window ############################
        time.sleep(2)
        self.log("Step 7: Closing report window...", "INFO")
        if not self.find_and_click('./imgdata/_6_btClose.png', confidence=0.8, retries=5):
            self.error_occurred.emit("Close Error", "Close button not found")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log(f"✓ Report saved successfully: {saveDT}.xlsx", "SUCCESS")
        return True

    def run(self):
        """Main thread execution"""
        self.log("Mesa thread started", "INFO")
        self.log("Waiting for serial trigger signal (MESA,MSS)...", "INFO")
        self.status_update.emit("Status: Waiting for trigger...")
        
        while self.running:
            if self.serialReceive == "MESA,MSS":
                self.log("✓ Received MESA,MSS trigger signal!", "SUCCESS")
                self.serialReceive = ""
                self.data_send.emit("MESA,MSR\n")
                
                all_success = True
                
                # Execute processes in order
                if self.do_egat_cal and all_success:
                    if not self.egatCalCurveProcess():
                        all_success = False
                        self.running = False
                        self.log("✗ EGAT Cal Curve failed - stopping", "ERROR")
                        break
                
                if self.do_egat_50kv and all_success:
                    if not self.egat50kVProcess():
                        all_success = False
                        self.running = False
                        self.log("✗ EGAT 50kV failed - stopping", "ERROR")
                        break
                
                if self.do_egat_15kv and all_success:
                    if not self.egat15kVProcess():
                        all_success = False
                        self.running = False
                        self.log("✗ EGAT 15kV failed - stopping", "ERROR")
                        break
                
                if all_success:
                    self.data_send.emit("MESA,MSD\n")
                    self.log("=" * 50, "SUCCESS")
                    self.log("ALL PROCESSES COMPLETED SUCCESSFULLY!", "SUCCESS")
                    self.log("=" * 50, "SUCCESS")
                    self.status_update.emit("Status: All Processes Completed")
                    self.running = False
                else:
                    return False
                    
            else:
                self.serialReceive = ""
            
            time.sleep(0.1)

    @pyqtSlot(str)
    def on_data_received(self, data):
        self.serialReceive = data
        self.log(f"Serial received: {data}", "INFO")
        self.status_update.emit(f"Serial: {data}")