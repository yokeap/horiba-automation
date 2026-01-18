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
    self.log("Warning: OpenCV (cv2, "INFO") not installed. Image detection will use basic matching without confidence levels.", "INFO")
    self.log("To install: pip install opencv-python", "INFO")
    
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
    error_occurred = pyqtSignal(str, str)  # Signal for error messages (title, message)
    process_completed = pyqtSignal(str)  # Signal for success messages
    status_update = pyqtSignal(str)  # Signal for status updates

    log_message = pyqtSignal(str, str)  # Signal for detailed logging (message, level)
    
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
        pyautogui.PAUSE = 0.5  # Add 0.5s pause between pyautogui actions
        pyautogui.FAILSAFE = True  # Move mouse to corner to abort

    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)


    def log(self, message, level="INFO"):
        """Helper method to emit log messages to GUI"""
        print(message)  # Still print to console for debugging
        self.log_message.emit(message, level)


    def find_and_click(self, image_path, confidence=0.8, retries=3, timeout=5, click_count=1):
        """
        Improved image detection and clicking with multiple strategies
        
        Args:
            image_path: Path to the image file
            confidence: Confidence level for image matching (0.0 to 1.0)
            retries: Number of retry attempts
            timeout: Maximum time to wait for image (seconds)
            click_count: Number of clicks (1 for single, 2 for double)
        
        Returns:
            True if successful, False otherwise
        """
        start_time = time.time()
        attempt = 0
        
        while attempt < retries and (time.time() - start_time) < timeout:
            try:
                # Try different confidence levels
                confidence_levels = [confidence, confidence - 0.1, confidence - 0.2]
                
                for conf in confidence_levels:
                    if conf < 0.5:
                        continue
                    
                    # Try to locate the image
                    location = pyautogui.locateOnScreen(image_path, confidence=conf)
                    
                    if location:
                        # Get center coordinates
                        center = pyautogui.center(location)
                        self.log(f"Found image: {image_path} at {center} with confidence {conf}", "INFO")
                        
                        # Click on the center
                        pyautogui.click(center.x, center.y, clicks=click_count)
                        time.sleep(0.5)
                        return True
                
                # If not found, wait a bit and retry
                self.log(f"Attempt {attempt + 1}/{retries}: Image not found: {image_path}", "INFO")
                time.sleep(1)
                attempt += 1
                
            except pyautogui.ImageNotFoundException:
                self.log(f"Attempt {attempt + 1}/{retries}: Image not found exception: {image_path}", "INFO")
                time.sleep(1)
                attempt += 1
            except Exception as e:
                error_msg = f"Error in find_and_click: {e}"
                print(error_msg)
                # self.error_occurred.emit("Detection Error", error_msg)
                time.sleep(1)
                attempt += 1
        
        error_msg = f"Failed to find image after {retries} attempts: {os.path.basename(image_path)}"
        print(error_msg)
        # self.error_occurred.emit("Image Not Found", error_msg)
        return False

    def wait_for_image(self, image_path, confidence=0.8, timeout=300, check_interval=5):
        """
        Wait for an image to appear on screen
        
        Args:
            image_path: Path to the image file
            confidence: Confidence level for image matching
            timeout: Maximum time to wait (seconds)
            check_interval: Time between checks (seconds)
        
        Returns:
            True if image found, False if timeout
        """
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                # Try different confidence levels
                confidence_levels = [confidence, confidence - 0.1, confidence - 0.2]
                
                for conf in confidence_levels:
                    if conf < 0.5:
                        continue
                    
                    location = pyautogui.locateOnScreen(image_path, confidence=conf)
                    if location:
                        self.log(f"Image appeared: {image_path} with confidence {conf}", "INFO")
                        return True
                
                elapsed = time.time() - start_time
                self.log(f"Waiting for image: {image_path} ({elapsed:.1f}/{timeout}s, "INFO")", "INFO")
                time.sleep(check_interval)
                
            except pyautogui.ImageNotFoundException:
                time.sleep(check_interval)
            except Exception as e:
                self.log(f"Error waiting for image: {e}", "INFO")
                time.sleep(check_interval)
        
        self.log(f"Timeout waiting for image: {image_path}", "INFO")
        return False

    def boot(self):
        """Bootup process with improved image detection"""
        self.log("Starting boot process...", "INFO")
        time.sleep(10)

        ################ skip calibration window ################### 
        self.log("Looking for calibration window...", "INFO")
        if not self.find_and_click('./imgdata/bt_cal_energy_copy.png', confidence=0.7, retries=3):
            self.log('Warning: Calibration window not found, continuing...', "INFO")
            # Don't return False here, as it might not always appear
        
        ################ skip cancel of whatever ###################
        time.sleep(1)
        self.log("Looking for cancel button...", "INFO")
        if not self.find_and_click('./imgdata/_0_btCancel.png', confidence=0.8, retries=3):
            self.error_occurred.emit("Boot Error", "Cannot find cancel button. Please ensure the application is running.")
            return False

        ################ project open process ###################
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
            print(error_msg)
            self.error_occurred.emit("Boot Error", error_msg)
            return False
        
        if self.do_warmup:
            self.log("\n========== Executing Warmup ==========", "INFO")
            self.status_update.emit("Running Warmup...")
            if not self.warmupProcess():
                self.error_occurred.emit("Boot Error", "Warmup failed - stopping thread.")
                self.status_update.emit("Status: Failed")
                self.log("Warmup failed - stopping thread", "INFO")
                return False
            
        self.data_send.emit("MESA,CHK\n")
        self.log("Boot process completed successfully", "INFO")
        return True
    
    def warmupProcess(self):
        """Warmup process implementation with improved detection"""
        self.log("Starting Warmup process...", "INFO")
        time.sleep(2)
        
        if not self.find_and_click('./imgdata/bt_warmup.png', confidence=0.8, retries=3):
            self.error_occurred.emit("Warmup Error", "Cannot start warmup process. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
         # Wait for process completion with improved detection
        self.log("Waiting for warmup process to complete...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=1300, check_interval=10):
            self.error_occurred.emit("Warmup Error", "Process timeout or incomplete. Ready signal not detected.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log("Warmup process completed", "INFO")
        self.log("\nWarmup process completed successfully", "INFO")
        return True
    
    def egat15kVProcess(self):
        """EGAT 15kV process implementation with improved detection"""
        self.log("Starting EGAT 15kV process...", "INFO")
        time.sleep(2)
        
        # Click on EGAT 15kV button
        if not self.find_and_click('./imgdata/bt_15kv.png', confidence=0.8, retries=3):
            self.error_occurred.emit("EGAT 15kV Error", "Cannot start EGAT 15kV process. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False
            
        time.sleep(10)
        
        # Wait for process completion with improved detection
        self.log("Waiting for EGAT 15kV process to complete...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=10):
            self.error_occurred.emit("EGAT 15kV Error", "Process timeout or incomplete. Ready signal not detected.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        # Save report
        if self.saveReport("EGAT-15kV"):
            self.log("\nEGAT 15kV process completed successfully", "INFO")
            return True
        return False
    
    def egat50kVProcess(self):
        """EGAT 50kV process implementation with improved detection"""
        self.log("Starting EGAT 50kV process...", "INFO")
        time.sleep(2)
        
        # Click on EGAT 50kV button
        if not self.find_and_click('./imgdata/bt_50kv.png', confidence=0.8, retries=3):
            self.error_occurred.emit("EGAT 50kV Error", "Cannot start EGAT 50kV process. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        time.sleep(10)
        
        # Wait for process completion with improved detection
        self.log("Waiting for EGAT 50kV process to complete...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=10):
            self.error_occurred.emit("EGAT 50kV Error", "Process timeout or incomplete. Ready signal not detected.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        # Save report
        if self.saveReport("EGAT-50kV"):
            self.log("\nEGAT 50kV process completed successfully", "INFO")
            return True
        return False
        
    def egatCalCurveProcess(self):
        """EGAT Calibration Curve process implementation with improved detection"""
        self.log("Starting EGAT Cal Curve process...", "INFO")
        time.sleep(2)
        
        ################# run egat cal curve ####################
        if not self.find_and_click('./imgdata/_2_btEGATCal.png', confidence=0.8, retries=3):
            self.error_occurred.emit("EGAT Cal Curve Error", "Cannot run EGAT Cal Curve. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False

        ################# check success with improved waiting #######################
        time.sleep(10)
        self.log("Waiting for EGAT Cal Curve process to complete...", "INFO")
        if not self.wait_for_image('./imgdata/_2_1_ready.png', confidence=0.8, timeout=300, check_interval=10):
            self.error_occurred.emit("EGAT Cal Curve Error", "Process timeout or incomplete. Ready signal not detected.")
            self.data_send.emit("MESA,ALM\n")
            return False

        # Save report
        self.log("Save report...", "INFO")
        if self.saveReport("EGAT-CAL"):
            self.log("\nEGAT Cal Curve process completed successfully", "INFO")
            return True
        return False
    
    def saveReport(self, process_name):
        """Common report saving function with improved detection"""
        self.log(f"Saving report for {process_name}...", "INFO")
        
        ################## report process #######################
        time.sleep(1)
        if not self.find_and_click('./imgdata/_3_btReport.png', confidence=0.8, retries=3):
            self.error_occurred.emit("Report Error", f"Cannot open report for {process_name}. Button not found.")
            self.data_send.emit("MESA,ALM\n")
            return False

        ################## save process #########################
        time.sleep(3)
        try:
            if not self.find_and_click('./imgdata/_4_btExport.png', confidence=0.8, retries=3):
                self.error_occurred.emit("Export Error", f"Cannot click export button for {process_name}.")
                self.data_send.emit("MESA,ALM\n")
                return False
            
            time.sleep(1)
            
            if not self.find_and_click('./imgdata/_5_ddExcel.png', confidence=0.8, retries=3):
                self.error_occurred.emit("Export Error", f"Cannot select Excel format for {process_name}.")
                self.data_send.emit("MESA,ALM\n")
                return False

            # Wait for Save As dialog
            if not autoit.win_wait_active("Save As", 5):
                self.error_occurred.emit("Save Error", f"Save As dialog did not appear for {process_name}.")
                self.data_send.emit("MESA,ALM\n")
                return False
            
            time.sleep(1)
            saveDT = "Report_" + process_name + "_" + datetime.now().strftime("%d-%m-%Y--%H-%M-%S")
            autoit.control_send("Save As", "Edit1", saveDT)
            time.sleep(1)
            autoit.control_click("Save As", "Button2")
            
        except pyautogui.ImageNotFoundException as e:
            error_msg = f'PyAutoGUI error in save process for {process_name}: {str(e)}'
            print(error_msg)
            self.error_occurred.emit("Save Error", error_msg)
            self.data_send.emit("MESA,ALM\n")
            return False
        except autoit.autoit.AutoItError as e:
            error_msg = f'AutoIt error in save process for {process_name}: {str(e)}'
            print(error_msg)
            self.error_occurred.emit("Save Error", error_msg)
            self.data_send.emit("MESA,ALM\n")
            return False
        except Exception as e:
            error_msg = f'Unexpected error in save process for {process_name}: {str(e)}'
            print(error_msg)
            self.error_occurred.emit("Save Error", error_msg)
            self.data_send.emit("MESA,ALM\n")
            return False

        ##################### close ############################
        time.sleep(2)
        if not self.find_and_click('./imgdata/_6_btClose.png', confidence=0.95, retries=3):
            self.error_occurred.emit("Close Error", f"Cannot close report window for {process_name}.")
            self.data_send.emit("MESA,ALM\n")
            return False
        
        self.log(f"{process_name} report saved successfully", "INFO")
        return True

    def run(self):
        """Main thread execution - runs selected processes in sequence"""
        while self.running:
            self.serialReceive = "MESA,MSS"
            if self.serialReceive == "MESA,MSS":
                mesa_status = True
                self.serialReceive = ""

                # check mesa lid closed status
                if self.find_and_click('./imgdata/bt_err_door.png', confidence=0.8, retries=1):
                    all_success = False
                    mesa_status = False
                    self.status_update.emit("Status: Failed")
                    self.log("MESA lid is open - stopping thread", "INFO")
                    self.data_send.emit("MESA,E02\n")
                    break

                 # check mesa USB status
                if self.find_and_click('./imgdata/bt_err_usb.png', confidence=0.8, retries=1):
                    all_success = False
                    mesa_status = False
                    self.status_update.emit("Status: Failed")
                    self.log("MESA USB error - stopping thread", "INFO")
                    self.data_send.emit("MESA,E03\n")
                    break

                if mesa_status:
                    self.data_send.emit("MESA,MSR\n")
                    all_success = True

                # Execute processes based on checkbox selections
                if self.do_egat_cal and all_success:
                    self.log("\n========== Executing EGAT Cal Curve ==========", "INFO")
                    self.status_update.emit("Running EGAT Cal Curve...")
                    if not self.egatCalCurveProcess():
                        all_success = False
                        self.running = False
                        self.status_update.emit("Status: Failed")
                        self.log("EGAT Cal Curve failed - stopping thread", "INFO")
                        break

                if self.do_egat_50kv and all_success:
                    self.log("\n========== Executing EGAT 50kV ==========", "INFO")
                    self.status_update.emit("Running EGAT 50kV...")
                    if not self.egat50kVProcess():
                        all_success = False
                        self.running = False
                        self.status_update.emit("Status: Failed")
                        self.log("EGAT 50kV failed - stopping thread", "INFO")
                        break
                
                if self.do_egat_15kv and all_success:
                    self.log("\n========== Executing EGAT 15kV ==========", "INFO")
                    self.status_update.emit("Running EGAT 15kV...")
                    if not self.egat15kVProcess():
                        all_success = False
                        self.running = False
                        self.status_update.emit("Status: Failed")
                        self.log("EGAT 15kV failed - stopping thread", "INFO")
                        break
                
                if all_success:
                    self.data_send.emit("MESA,MSD\n")
                    # self.status_update.emit("Status: All Completed Successfully")
                    self.log("\n========== All selected processes completed successfully ==========", "INFO")
                    self.running = False        # for debugging
                else:
                    return False
                    
            else:
                self.serialReceive = ""
                self.running = False
            
            time.sleep(0.1)  # Small delay to prevent CPU spinning

    @pyqtSlot(str)
    def on_data_received(self, data):
        self.serialReceive = data
        self.log(f"Serial received: {self.serialReceive}", "INFO")