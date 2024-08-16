#!/usr/bin/env python3
# coding=utf-8

import time
from Arm_Lib import Arm_Device
import sys
import cffi

# Update this path to point to the correct Leap SDK directory
sys.path.insert(0, "/path/to/LeapSDK")

import leap
from leap import datatypes as ldt
from leap import Listener
from leap.datatypes import Hand as LeapHand

# Initialize cffi to handle C structures
ffi = cffi.FFI()

class FrameData:
    """Wrapper which owns all the data required to read the Frame

    A LEAP_TRACKING_EVENT has a fixed size, but some fields are pointers to memory stored
    outside of the struct. This means the size required for all the information about a
    frame is larger than the size of the struct.

    This wrapper owns the buffer required for all of that data. Reading attributes or
    items from this wrapper returns the corresponding item or wrapper on the underlying
    LEAP_TRACKING_EVENT.

    It is intended to be used in the TrackingEvent constructor.
    """

    def __init__(self, size):
        self._buffer = ffi.new("char[]", size)
        self._frame_ptr = ffi.cast("LEAP_TRACKING_EVENT*", self._buffer)

    def __getattr__(self, name):
        return getattr(self._frame_ptr, name)

    def __getitem__(self, key):
        return self._frame_ptr[key]

    def frame_ptr(self):
        return self._frame_ptr


class PinchingListener(Listener):
    def __init__(self, buffer_size):
        super(PinchingListener, self).__init__()
        self.servo_angles = [0, 0, 0, 0]  # Initial angles for the servos
        self.is_pinching = [False] * 4  # Track the current pinch state for each finger pair
        self.frame_data = FrameData(buffer_size)

    def on_tracking_event(self, event):
        for hand in event.hands:
            leap_hand = LeapHand(ffi.cast("LEAP_HAND*", hand))

            # Thumb and various fingers
            thumb = leap_hand.thumb.distal.next_joint

            digits = [
                { 'name': 'index', 'joint': leap_hand.index.distal.next_joint, 'servo_id': 1, 'pinch_idx': 0 },
                { 'name': 'middle', 'joint': leap_hand.middle.distal.next_joint, 'servo_id': 2, 'pinch_idx': 1 },
                { 'name': 'ring', 'joint': leap_hand.ring.distal.next_joint, 'servo_id': 3, 'pinch_idx': 2 },
                { 'name': 'pinky', 'joint': leap_hand.pinky.distal.next_joint, 'servo_id': 4, 'pinch_idx': 3 }
            ]

            for digit in digits:
                pinching = fingers_pinching(thumb, digit['joint'])

                if pinching and not self.is_pinching[digit['pinch_idx']]:
                    print(f"{digit['name']} and thumb pinching detected!")
                    self.servo_angles[digit['pinch_idx']] = (self.servo_angles[digit['pinch_idx']] + 60) % 180
                    control_single_servo(digit['servo_id'], self.servo_angles[digit['pinch_idx']])
                    self.is_pinching[digit['pinch_idx']] = True
                elif not pinching:
                    self.is_pinching[digit['pinch_idx']] = False

def control_single_servo(servo_id, angle, duration=400):
    Arm.Arm_serial_servo_write(servo_id, angle, duration)
    time.sleep(0.7)

def fingers_pinching(thumb, finger):
    diff = list(map(abs, [thumb.x - finger.x, thumb.y - finger.y, thumb.z - finger.z]))
    return diff[0] < 20 and diff[1] < 20 and diff[2] < 20

def main():
    buffer_size = 1024 * 1024  # Adjust as needed based on your data requirements
    listener = PinchingListener(buffer_size)

    connection = leap.Connection()
    connection.add_listener(listener)

    try:
        with connection.open():
            print("Connection opened. Control the servos with pinch gestures.")
            while True:
                time.sleep(0.7)
    except KeyboardInterrupt:
        print("Program closed!")
    finally:
        del Arm

if __name__ == "__main__":
    Arm = Arm_Device()
    time.sleep(0.1)
    main()