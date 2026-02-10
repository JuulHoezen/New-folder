import cv2
import math
import pygame
from constants import *


class HandGestureDetector:
    """Hand gesture detector using MediaPipe."""

    def __init__(self):
        self.hand_x = 0.5
        self.gesture = "none"
        self.hand_detected = False
        self.frame_rgb = None
        self.landmarks = None
        self.cap = None
        self.use_mediapipe = False
        
        # Try to initialize MediaPipe
        try:
            import mediapipe as mp
            self.mp_hands = mp.solutions.hands
            self.hands = self.mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,
                min_detection_confidence=0.7,
                min_tracking_confidence=0.6,
            )
            self.use_mediapipe = True
            print("INFO: MediaPipe hand detection initialized")
        except Exception as e:
            print(f"ERROR: MediaPipe not available ({type(e).__name__})")
            self.use_mediapipe = False
        
        # Try to open webcam
        try:
            self.cap = cv2.VideoCapture(0)
            if self.cap and self.cap.isOpened():
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                print("INFO: Webcam opened successfully")
            else:
                self.cap = None
                print("ERROR: Webcam not available")
        except Exception as e:
            print(f"ERROR: Webcam unavailable ({e})")
            self.cap = None

    def _is_finger_extended(self, lm, tip_id, pip_id, mcp_id):
        """Check if a finger is extended."""
        tip = lm[tip_id]
        pip_ = lm[pip_id]
        mcp = lm[mcp_id]
        
        tip_dist = math.hypot(tip.x - lm[0].x, tip.y - lm[0].y)
        pip_dist = math.hypot(pip_.x - lm[0].x, pip_.y - lm[0].y)
        return tip_dist > pip_dist

    def _is_thumb_extended(self, lm):
        """Check if thumb is extended."""
        thumb_tip = lm[4]
        thumb_ip = lm[3]
        index_mcp = lm[5]
        
        tip_dist = math.hypot(thumb_tip.x - index_mcp.x, thumb_tip.y - index_mcp.y)
        ip_dist = math.hypot(thumb_ip.x - index_mcp.x, thumb_ip.y - index_mcp.y)
        return tip_dist > ip_dist

    def _classify_gesture(self, lm):
        """Classify gesture based on extended fingers."""
        thumb = self._is_thumb_extended(lm)
        index = self._is_finger_extended(lm, 8, 6, 5)
        middle = self._is_finger_extended(lm, 12, 10, 9)
        ring = self._is_finger_extended(lm, 16, 14, 13)
        pinky = self._is_finger_extended(lm, 20, 18, 17)

        extended = [thumb, index, middle, ring, pinky]
        count = sum(extended)

        if count >= 5:
            return "shotgun"
        if index and middle and not ring and not pinky:
            return "burst"
        if index and not middle and not ring and not pinky:
            return "single"
        return "none"

    def update(self):
        """Update hand position and gesture from webcam."""
        # Only use webcam - no keyboard fallback
        if not self.use_mediapipe or not self.cap:
            return
        
        ret, frame = self.cap.read()
        if not ret:
            return

        # Mirror the frame
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        try:
            # Process with MediaPipe
            results = self.hands.process(rgb)
            self.frame_rgb = rgb
            
            if results.multi_hand_landmarks:
                hand_lm = results.multi_hand_landmarks[0]
                lm = hand_lm.landmark
                self.landmarks = lm
                self.hand_detected = True
                
                # Update hand position (wrist x position)
                self.hand_x = lm[0].x
                
                # Classify gesture
                self.gesture = self._classify_gesture(lm)
            else:
                # No hand detected
                self.hand_detected = False
                self.landmarks = None
                self.gesture = "none"
        except Exception as e:
            print(f"Hand detection error: {e}")
            self.frame_rgb = rgb
            self.hand_detected = False
            self.landmarks = None
            self.gesture = "none"

    def get_pip_surface(self):
        """Return pygame surface of camera feed."""
        if self.frame_rgb is None:
            surf = pygame.Surface((PIP_W, PIP_H))
            surf.fill((30, 30, 30))
            return surf

        small = cv2.resize(self.frame_rgb, (PIP_W, PIP_H))

        if self.landmarks is not None:
            h, w = PIP_H, PIP_W
            lm = self.landmarks
            
            connections = [
                (0, 1), (1, 2), (2, 3), (3, 4),
                (0, 5), (5, 6), (6, 7), (7, 8),
                (0, 9), (9, 10), (10, 11), (11, 12),
                (0, 13), (13, 14), (14, 15), (15, 16),
                (0, 17), (17, 18), (18, 19), (19, 20),
                (5, 9), (9, 13), (13, 17),
            ]
            
            for (a, b) in connections:
                x1, y1 = int(lm[a].x * w), int(lm[a].y * h)
                x2, y2 = int(lm[b].x * w), int(lm[b].y * h)
                cv2.line(small, (x1, y1), (x2, y2), (0, 255, 100), 1)
            
            for i in range(21):
                cx, cy = int(lm[i].x * w), int(lm[i].y * h)
                cv2.circle(small, (cx, cy), 2, (255, 255, 255), -1)

        surf = pygame.image.frombuffer(small.tobytes(), (PIP_W, PIP_H), "RGB")
        return surf

    def release(self):
        if self.cap:
            self.cap.release()
        if self.use_mediapipe and hasattr(self, 'hands'):
            self.hands.close()
