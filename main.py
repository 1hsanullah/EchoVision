import sys
import threading
from PyQt5 import QtWidgets
from gui_file import GUI_class  # Assuming GUI_class is defined in gui_file.py
from detect_speech import Speech_to_text  # Make sure to adjust imports based on your actual file structure

def run_speech_to_text(stop_event):
    """
    This function creates an instance of the Speech_to_text class
    and starts the speech recognition process.
    It accepts a threading.Event() to signal when to stop.
    """
    speech_to_text_instance = Speech_to_text(stop_event)
    speech_to_text_instance.speech_to_text()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = GUI_class()

    # Use the existing speech_to_text_instance from the GUI.
    speech_to_text_thread = threading.Thread(target=ui.speech_to_text_instance.speech_to_text)

    # Start the speech recognition thread.
    speech_to_text_thread.start()

    # Run the Qt application
    app.exec_()

    # After closing the GUI, ensure the speech recognition thread also exits
    ui.stop_event.set()  # Ensure the event is set to stop the speech thread
    speech_to_text_thread.join()  # Wait for the thread to finish

    print("Both threads have finished executing.")

