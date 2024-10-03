import speech_recognition as sr
import os
import pyautogui
import pygame
import threading
from eye_controller import EyeControlledMouse

class Speech_to_text:
    def __init__(self, stop_event):
        self.recognizer = sr.Recognizer()
        self.text = ""
        self.permission = False
        self.stop_event = stop_event
        self.start_typing_sound = "audio\\Typing.mp3"
        self.stop_typing_sound = "audio\\Stoptype.mp3"
        self.calibrate_sound = "audio\\Calibrate.mp3"
        self.eye_controller = EyeControlledMouse()
        self.last_command_time = None
        self.timer = None
        self.phrase_time_limit = 3
        self.scroll_amount = 500
        self.commands = {
            "enter": lambda: pyautogui.press('enter'),
            "clear": lambda: pyautogui.hotkey('ctrl', 'a', 'backspace'),
            # Add more special commands as needed
        }

        # Initialize pygame mixer
        pygame.mixer.init()
        self.start_sound = pygame.mixer.Sound(self.start_typing_sound)
        self.stop_sound = pygame.mixer.Sound(self.stop_typing_sound)
        self.calibrate_sound = pygame.mixer.Sound(self.calibrate_sound)

    def set_scroll_amount(self, amount):
        self.scroll_amount = amount
        print(f"Scroll amount successfully updated to: {amount}")

    def set_phrase_time_limit(self, limit):
        self.phrase_time_limit = limit

    def play_start_sound(self):
        self.start_sound.play()

    def play_stop_sound(self):
        self.stop_sound.play()
        
    def reset_permission(self):
        if self.permission:
            self.play_stop_sound()
            self.permission = False
            print("Typing mode deactivated due to inactivity.")

    def update_timer(self):
        if self.timer is not None:
            self.timer.cancel()
        self.timer = threading.Timer(20.0, self.reset_permission)
        self.timer.start()

    def speech_to_text(self):
        last_print = None
        while not self.stop_event.is_set():
            try:
                with sr.Microphone() as mic:
                    current_message = "Typing..." if self.permission else "Say 'type' or 'start' to start typing..."
                    if current_message != last_print:
                        print(current_message)
                        last_print = current_message

                    audio = self.recognizer.listen(mic, phrase_time_limit=self.phrase_time_limit)
                    text = self.recognizer.recognize_google(audio).lower()
                    self.update_timer()  # Reset the timer every time a command is processed
                    
                    if "calibrate" in text:
                        self.calibrate_sound.play()
                        self.eye_controller.calibrate()
                        continue

                    if "scroll down" in text:
                        print(f"Scrolling down by {self.scroll_amount}")  # Debug to see actual scroll amount used
                        pyautogui.scroll(-self.scroll_amount)
                    elif "scroll up" in text:
                        print(f"Scrolling up by {self.scroll_amount}")  # Debug to see actual scroll amount used
                        pyautogui.scroll(self.scroll_amount)

                    if "type" in text or "start" in text:
                        if not self.permission:
                            self.play_start_sound()
                        self.permission = True
                        print("Typing mode activated.")
                        continue
                    
                    elif "stop typing" in text:
                        self.reset_permission()
                        print("Typing mode deactivated.")
                        continue

                    if self.permission:
                        if text in self.commands:
                            self.commands[text]()
                        else:
                            pyautogui.write(text + " ")
                        print(text) 
                        self.update_timer()
                        # Print recognized text only when permission is granted

            except sr.UnknownValueError:
                pass  # No speech was understood
            except sr.RequestError:
                if last_print != "API Error":
                    print("API is unreachable, please check your internet connection.")
                    last_print = "API Error"
            
            if self.stop_event.is_set():
                if self.timer is not None:
                    self.timer.cancel()
                print("Stopping speech recognition.")
                break

