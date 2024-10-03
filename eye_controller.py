import cv2
import mediapipe as mp
import pyautogui
import time

pyautogui.FAILSAFE = False


class EyeControlledMouse:
    def __init__(self):
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(refine_landmarks=True)
        self.screen_w, self.screen_h = pyautogui.size()
        self.prev_x = self.screen_w / 2  # Initialize cursor at the center of the screen
        self.prev_y = self.screen_h / 2
        self.move_speed = 5
        self.click_sesitivity = 0.008

        self.alpha = 0.2  # Low-pass filter smoothing factor
        self.prev_smoothed_x = self.prev_x
        self.prev_smoothed_y = self.prev_y

        # Debounce variables
        self.last_click_time = 0
        self.click_debounce_threshold = 0.5  # 500 milliseconds debounce time
        
    def set_click_sensitivity(self, sensitivity):
        self.click_sensitivity = sensitivity
    
    
    def apply_low_pass_filter(self, current_x, current_y):
        smoothed_x = (1 - self.alpha) * self.prev_smoothed_x + self.alpha * current_x
        smoothed_y = (1 - self.alpha) * self.prev_smoothed_y + self.alpha * current_y
        self.prev_smoothed_x = smoothed_x
        self.prev_smoothed_y = smoothed_y

        return smoothed_x, smoothed_y

    def run(self, frame):
        try:
            frame_h, frame_w, _ = frame.shape
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            output = self.face_mesh.process(rgb_frame)

            if output.multi_face_landmarks:
                landmarks = output.multi_face_landmarks[0].landmark

                landmark = landmarks[473]
                screen_x = min(max(landmark.x * self.screen_w, 0), self.screen_w)
                screen_y = min(max(landmark.y * self.screen_h, 0), self.screen_h)

                smoothed_x, smoothed_y = self.apply_low_pass_filter(screen_x, screen_y)

                if self.prev_x is not None and self.prev_y is not None:
                    if smoothed_x < self.screen_w and smoothed_y < self.screen_h:
                        move_x = (smoothed_x - self.prev_x) * self.move_speed
                        move_y = (smoothed_y - self.prev_y) * self.move_speed
                        pyautogui.moveRel(move_x, move_y)

                self.prev_x = smoothed_x
                self.prev_y = smoothed_y

                left = [landmarks[145], landmarks[159]]
                right = [landmarks[386], landmarks[374]]

                for landmark in left + right:
                    x = int(landmark.x * frame_w)
                    y = int(landmark.y * frame_h)
                    cv2.circle(frame, (x, y), 3, (0, 255, 255))

                current_time = time.time()
                if (left[0].y - left[1].y) < self.click_sensitivity and (current_time - self.last_click_time > self.click_debounce_threshold):
                    pyautogui.click()
                    self.last_click_time = current_time

                elif (right[1].y - right[0].y) < self.click_sensitivity and (current_time - self.last_click_time > self.click_debounce_threshold):
                    pyautogui.click(button="right")
                    self.last_click_time = current_time

            return frame

        except Exception as e:
            print(f"Encountered error in EyeControlledMouse run: {e}")
            return frame

    def change_speed(self, value):
        self.move_speed = value

    def calibrate(self):
        center_x = int(self.screen_w / 2)
        center_y = int(self.screen_h / 2)
        pyautogui.moveTo(center_x, center_y)
        
        # Lock the mouse position for 3 seconds
        start_time = time.time()
        while time.time() - start_time < 3.5:
            pyautogui.moveTo(center_x, center_y)
            time.sleep(0.1)  # Sleep for 100 ms to prevent too high CPU usage

