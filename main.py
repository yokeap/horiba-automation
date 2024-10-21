import autoit
import pyautogui
import time

class Cal():
    def __init__(self):
        super().__init__()

    def process(self):
        autoit.win_wait_active("[CLASS:Calculator]", 3)
        try:
            button7location = pyautogui.locateOnScreen('./imgdata/calc7key.png')
            pyautogui.click('./imgdata/calc7key.png')
        except pyautogui.ImageNotFoundException:
            autoit.win_close("[CLASS:Calculator]")
            print('ImageNotFoundException: image not found')


calProcessID = autoit.run("Calc.exe")
# className = "[Class:#" + str(calProcessID) + "]"
# print(className)
calApp = Cal()
calApp.process()

    

# class Cat:
#     def __init__(self, name, age):
#         self.name = name
#         self.age = age

#     def run(self)


