class Mesa():
    def __init__(self):
        super().__init__()

    def process(self):
        # bootup process
        time.sleep(10) 
        try:
            pyautogui.click('./imgdata/_0_btCancel.png')
        except pyautogui.ImageNotFoundException:
            print('Error: Start program')
            # send error to arduino

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