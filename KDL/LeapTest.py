#!/usr/bin/env python3
# coding=utf-8
import time
from Arm_Lib import Arm_Device
import sys

sys.path.insert(0, "/home/jetson/Downloads/ultraleap-hand-tracking-service_5.17.1.0-a9f25232-arm64/LeapSDK/lib/cmake/LeapSDK")

import leap
from leap import datatypes as ldt
from leap import Listener

# Create a robotic arm object
Arm = Arm_Device()
time.sleep(0.1)

# Function to control a single servo
def control_single_servo(servo_id, angle, duration=400):
    Arm.Arm_serial_servo_write(servo_id, angle, duration)
    time.sleep(0.7)

# Function to determine if fingers are pinching
def fingers_pinching(thumb: ldt.Vector, index: ldt.Vector) -> bool:
    diff = list(map(abs, [thumb.x - index.x, thumb.y - index.y, thumb.z - index.z]))
    return diff[0] < 20 and diff[1] < 20 and diff[2] < 20

class PinchingListener(Listener):
    def __init__(self, servo_id):
        super(PinchingListener, self).__init__()
        self.servo_id = servo_id
        self.servo_angle = 0  # Initial angle for the servo
        self.is_pinching = False  # Track the current pinch state
        print("PinchingListener initialized")

    def on_tracking_event(self, event):
        for hand in event.hands:
            thumb = hand.digits[0].distal.next_joint
            index = hand.digits[1].distal.next_joint

            pinching = fingers_pinching(thumb, index)

            if pinching and not self.is_pinching:
                # Pinch detected and it's a new pinch (wasn't pinching before)
                print("Pinching detected!")
                self.servo_angle = (self.servo_angle + 60) % 180  # Adjust the servo angle
                control_single_servo(self.servo_id, self.servo_angle)
                self.is_pinching = True  # Update the pinch state
            elif not pinching:
                # Not pinching, reset the state
                self.is_pinching = False

def main():
    servo_id = 1  # ID of the servo to control
    listener = PinchingListener(servo_id)

    connection = leap.Connection()
    connection.add_listener(listener)

    try:
        with connection.open():
            print("Connection opened. Control the servo with pinch gestures.")
            while True:
                time.sleep(0.7)

    except KeyboardInterrupt:
        print("Program closed!")
    finally:
        del Arm  # Release Arm object

if __name__ == "__main__":
    main()



