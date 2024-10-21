import autoit
import pyautogui
import time
import threading
from datetime import datetime

class mesa:
    def __init__(self):
        # super().__init__()
        self.stop_event = threading.Event()
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
    
        self.init = True
        self.mesaThread = threading.Thread(target=self.run)
        self.mesaThread.daemon = True
        

    def process(self):
        
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

    def run(self):
        while not self.stop_event.is_set():
            if self.process() == False:
                self.stop_event.set()
                print("Thread stop!") 

    def start_thread(self):        
        self.mesaThread.start()

    def stop_thread(self):
        self.stop_event.set()
