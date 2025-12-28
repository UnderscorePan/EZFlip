import threading
import time

import cv2
import mediapipe as mp


mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils
previous_finger_count = 0


def count_fingers(hand_landmarks):
    finger_tips = [mp_hands.HandLandmark.INDEX_FINGER_TIP,
                   mp_hands.HandLandmark.MIDDLE_FINGER_TIP,
                   mp_hands.HandLandmark.RING_FINGER_TIP,
                   mp_hands.HandLandmark.PINKY_TIP]

    count = 0
    for tip in finger_tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            count += 1
    return count


def gesture_control(on_prev, on_next, on_flip):
    global previous_finger_count
    cap = cv2.VideoCapture(0)

    gesture_active = False
    last_gesture_time = time.time()
    cooldown_period = 2.0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        current_finger_count = 0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                current_finger_count = count_fingers(hand_landmarks)

                if not gesture_active and (time.time() - last_gesture_time > cooldown_period):
                    if current_finger_count == 1:
                        on_prev()
                        gesture_active = True
                        last_gesture_time = time.time()
                    elif current_finger_count == 2:
                        on_next()
                        gesture_active = True
                        last_gesture_time = time.time()
                    elif current_finger_count == 3:
                        on_flip()
                        gesture_active = True
                        last_gesture_time = time.time()

                if current_finger_count == 0:
                    gesture_active = False

                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        else:
            gesture_active = False

        cv2.imshow('Gesture Control', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def start_gesture_control(on_prev, on_next, on_flip):
    gesture_thread = threading.Thread(target=gesture_control, args=(on_prev, on_next, on_flip))
    gesture_thread.start()
    return gesture_thread
