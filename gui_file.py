from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtGui import QImage, QPixmap
import cv2
import sys
from eye_controller import EyeControlledMouse
from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
import threading
from detect_speech import Speech_to_text

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)
    stop_loop = True

    def __init__(self, mainclass):
        super().__init__()
        self.mainclass = mainclass

    def run(self):
        self.cap = cv2.VideoCapture(0)
        while self.stop_loop:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = cv2.flip(frame, 1)
                frame = self.mainclass._eyecontroller.run(frame)
                h, w, ch = frame.shape
                bytes_per_line = ch * w
                convert_to_Qt_format = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
                p = convert_to_Qt_format.scaled(640, 480)
                self.changePixmap.emit(p)
        self.cleanup()

    def cleanup(self):
        self.cap.release()
        cv2.destroyAllWindows()
        self.mainclass.label.clear()

class AutoCloseMessageBox(QtWidgets.QMessageBox):
    def __init__(self, timeout=3, parent=None):
        super(AutoCloseMessageBox, self).__init__(parent)
        self.timeout = timeout
        self.setWindowTitle("Calibration")
        self.setAutoClose(True)

    def setAutoClose(self, value):
        if value:
            self.timer = QtCore.QTimer(self)
            self.timer.setInterval(self.timeout * 1000)
            self.timer.setSingleShot(True)
            self.timer.timeout.connect(self.accept)
            self.timer.start()
        else:
            self.timer.stop()

    def closeEvent(self, event):
        self.setAutoClose(False)
        super(AutoCloseMessageBox, self).closeEvent(event)

class GUI_class(QtWidgets.QWidget):
    def __init__(self):
        super(GUI_class, self).__init__()
        self._eyecontroller = EyeControlledMouse()
        self.setupUi()
        self.load_styles()
        self.stop_event = threading.Event()
        self.speech_to_text_instance = Speech_to_text(self.stop_event)

    def load_styles(self):
        with open('style.qss', 'r') as file:
            self.setStyleSheet(file.read())

    def setupUi(self):
        self.resize(600, 600)
        self.gridLayout = QtWidgets.QGridLayout(self)

        self.tabWidget = QtWidgets.QTabWidget(self)
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        # Main Tab
        self.mainWidget = QtWidgets.QWidget()
        self.tabWidget.addTab(self.mainWidget, "EchoVision")
        self.mainLayout = QtWidgets.QVBoxLayout(self.mainWidget)

        # Label for displaying camera feed
        self.label = QtWidgets.QLabel(self.mainWidget)
        self.label.setMinimumSize(640, 480)
        self.mainLayout.addWidget(self.label)
        
        # Instruction Label for Speech Commands
        self.instructionLabel = QtWidgets.QLabel("Say 'type' or 'start' to start typing...")
        self.instructionLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.mainLayout.addWidget(self.instructionLabel)

        # Button to start camera
        self.pushButton = QtWidgets.QPushButton("Start", clicked=self.start_work)
        self.mainLayout.addWidget(self.pushButton)

        # Button to calibrate eye controller
        self.pushButton_2 = QtWidgets.QPushButton("Calibrate", clicked=self.show_calibration_message)
        self.mainLayout.addWidget(self.pushButton_2)

        # Settings Tab
        self.settingsWidget = QtWidgets.QWidget()
        self.tabWidget.addTab(self.settingsWidget, "Settings")
        self.settingsLayout = QtWidgets.QVBoxLayout(self.settingsWidget)

        # Mouse Speed Dropdown
        self.mouseSpeedLabel = QtWidgets.QLabel("Mouse Sensitivity:")
        self.mouseSpeedDropdown = QtWidgets.QComboBox()
        for speed in range(1, 11):
            self.mouseSpeedDropdown.addItem(str(speed))
        self.mouseSpeedDropdown.setCurrentIndex(4)
        self.mouseSpeedDropdown.currentIndexChanged.connect(self.dropdownChange)
        self.settingsLayout.addWidget(self.mouseSpeedLabel)
        self.settingsLayout.addWidget(self.mouseSpeedDropdown)
        
        # Click Sensitivity Dropdown
        self.clickSensitivityLabel = QtWidgets.QLabel("Click Sensitivity:")
        self.clickSensitivityDropdown = QtWidgets.QComboBox()
        self.clickSensitivityDropdown.addItem("Low", 0.004)
        self.clickSensitivityDropdown.addItem("Medium", 0.008)  # default
        self.clickSensitivityDropdown.addItem("High", 0.012)
        self.clickSensitivityDropdown.currentIndexChanged.connect(self.updateClickSensitivity)
        self.settingsLayout.addWidget(self.clickSensitivityLabel)
        self.settingsLayout.addWidget(self.clickSensitivityDropdown)
        self.clickSensitivityDropdown.setCurrentIndex(1)  # Set "Medium" as the default

        # Phrase Time Limit Dropdown
        self.phraseTimeLimitLabel = QtWidgets.QLabel("Typing Time:")
        self.phraseTimeLimitDropdown = QtWidgets.QComboBox()
        self.phraseTimeLimitDropdown.addItem("Short", 3)
        self.phraseTimeLimitDropdown.addItem("Medium", 5)
        self.phraseTimeLimitDropdown.addItem("Long", 10)
        self.phraseTimeLimitDropdown.currentIndexChanged.connect(self.updatePhraseTimeLimit)
        self.settingsLayout.addWidget(self.phraseTimeLimitLabel)
        self.settingsLayout.addWidget(self.phraseTimeLimitDropdown)
        self.phraseTimeLimitDropdown.setCurrentIndex(0)  # Set "Short" as the default
        
        # Scroll Amount Dropdown
        self.scrollAmountLabel = QtWidgets.QLabel("Scroll Amount:")
        self.scrollAmountDropdown = QtWidgets.QComboBox()
        # Add predefined scroll amounts here
        self.scrollAmountDropdown.addItem("500 Pixels", 500)
        self.scrollAmountDropdown.addItem("1000 Pixels", 1000)
        self.scrollAmountDropdown.addItem("2000 Pixels", 2000)
        self.scrollAmountDropdown.addItem("3000 Pixels", 3000)
        self.scrollAmountDropdown.addItem("4000 Pixels", 4000)
        self.scrollAmountDropdown.addItem("5000 Pixels", 5000)
        self.scrollAmountDropdown.addItem("10000 Pixels", 10000)
        # Connect the dropdown change to a method
        self.scrollAmountDropdown.currentIndexChanged.connect(self.updateScrollAmountFromDropdown)
        self.settingsLayout.addWidget(self.scrollAmountLabel)
        self.settingsLayout.addWidget(self.scrollAmountDropdown)
        
        # Command Guide Label
        self.commandGuideLabel = QtWidgets.QLabel("Commands:\n"
                                                  "-  'Type' or 'Start': Activate typing mode\n"
                                                  "-  'stop typing': Deactivate typing mode\n"
                                                  "-  'calibrate': Calibrate eye control\n"
                                                  "-  'scroll up/down': Scroll screen\n"
                                                  "-  Special commands like 'enter', 'clear'\n"
                                                  "Say commands clearly to operate.")
        self.commandGuideLabel.setAlignment(QtCore.Qt.AlignLeft)
        self.settingsLayout.addWidget(self.commandGuideLabel)

        # Spacer for future settings
        self.spacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.settingsLayout.addItem(self.spacer)

        self.retranslateUi()
        QtCore.QMetaObject.connectSlotsByName(self)
        self.show()
           
        
    def updateClickSensitivity(self):
        sensitivity = self.clickSensitivityDropdown.currentData()
        self._eyecontroller.set_click_sensitivity(sensitivity)

    def updatePhraseTimeLimit(self):
        limit = self.phraseTimeLimitDropdown.currentData()
        self.speech_to_text_instance.set_phrase_time_limit(limit)
        
    def updateScrollAmountFromDropdown(self):
        # Retrieve the selected scroll amount from the dropdown's current data
        new_scroll_amount = self.scrollAmountDropdown.currentData()
        print(f"Attempting to update scroll amount to: {new_scroll_amount}")
        
        # Update the scroll amount in the Speech_to_text instance
        self.speech_to_text_instance.set_scroll_amount(new_scroll_amount)
        print(f"Scroll amount set to {new_scroll_amount}")




    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.setWindowTitle(_translate("Form", "EchoVision"))
        self.pushButton.setText(_translate("Form", "Start"))
        self.pushButton_2.setText(_translate("Form", "Calibrate"))

    def dropdownChange(self):
        speed = int(self.mouseSpeedDropdown.currentText())
        self._eyecontroller.change_speed(speed)

    def start_work(self):
        if hasattr(self, 'th') and self.camera_flag:
            self.th.stop_loop = False
            self.camera_flag = False
            self.pushButton.setText("Start")
        else:
            self.th = Thread(self)
            self.th.changePixmap.connect(self.setImage)
            self.th.start()
            self.camera_flag = True
            self.pushButton.setText("Stop")

    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image).scaled(self.label.size(), QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation))

    def show_calibration_message(self):
        msgBox = AutoCloseMessageBox(3, self)
        msgBox.setIcon(QtWidgets.QMessageBox.Information)
        msgBox.setText("Calibration process has started.")
        msgBox.setInformativeText("Please align your eyes and head with the center of the screen and cursor.")
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msgBox.exec_()
        self._eyecontroller.calibrate()

def start_gui():
    app = QtWidgets.QApplication(sys.argv)
    ui = GUI_class()
    sys.exit(app.exec_())

