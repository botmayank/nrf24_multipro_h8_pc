#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
syma_controller.py

Created on Fri Sep 14 2018 23:55:11 2018

@author: botmayank
"""
import time

import serial

INPUT_MIN = 1000
INPUT_MID = 1500
INPUT_MAX = 2000

THROTTLE_GO = 1530

# deltas to increase/decrease RC inputs
tg = 50
ag = 20
eg = 20
rg = 20


class SymaController:
    """ Syma Controller class """

    throttle = INPUT_MIN  # thrust
    aileron = INPUT_MID  # roll
    elevator = INPUT_MID  # pitch
    rudder = INPUT_MID  # yaw
    arduino = None
    port = "/dev/ttyUSB0"

    def __init__(self, port):
        self.port = port

        try:
            self.arduino = serial.Serial(port, 115200, timeout=0.01)
            self.arduino.inWaiting()
        except:
            exit("No serial connection")

        time.sleep(1)  # give the connection a second to settle
        self.arduino.write(("1000, 1500, 1500, 1500\n").encode())

    def __del__(self):
        # close the connection
        self.arduino.close()
        # re-open the serial port which will also reset the Arduino Uno and
        # this forces the quadcopter to power off when the radio loses conection. 
        self.arduino = serial.Serial(self.port, 115200, timeout=.01)
        # close it again so it can be reopened the next time it is run.    
        self.arduino.close()

    def _clamp_input(self, n):
        return max(INPUT_MIN, min(n, INPUT_MAX))

    def _get_mapped_value(self, n):
        """
        :param n: value between -1 and 1
        :return: the mapped value from [-1,1] to [MIN, MAX]
        """
        return INPUT_MIN + (INPUT_MAX - INPUT_MIN) * ((1.0 + n) / 2.0)

    def _update_input(self, input_type, val, delta):
        # global throttle, aileron, elevator, rudder
        temp = val + delta

        if input_type == "thrust":
            self.throttle = self._clamp_input(temp)
        elif input_type == "roll":
            self.aileron = self._clamp_input(temp)
        elif input_type == "pitch":
            self.elevator = self._clamp_input(temp)
        elif input_type == "yaw":
            self.rudder = self._clamp_input(temp)

    def delta_roll(self, dir, delta=ag):
        if dir == "right":
            self._update_input("roll", self.aileron, +delta)
        elif dir == "left":
            self._update_input("roll", self.aileron, -delta)

    def delta_pitch(self, dir, delta=eg):
        if dir == "forward":
            self._update_input("pitch", self.elevator, +delta)
        elif dir == "back":
            self._update_input("pitch", self.elevator, -delta)

    def delta_yaw(self, dir, delta=rg):
        if dir == "ccw":
            self._update_input("yaw", self.rudder, -delta)
        elif dir == "cw":
            self._update_input("yaw", self.rudder, +delta)

    def delta_thrust(self, dir, delta=tg):
        if dir == "up":
            self._update_input("thrust", self.throttle, +delta)
        elif dir == "down":
            self._update_input("thrust", self.throttle, -delta)
        elif dir == "mid":
            self.throttle = INPUT_MID

    def delta_thrust_relative(self, gain):
        """
        :param gain: value between [-1,1] of change thrust_gain with which delta increases/decreases
        """
        self._update_input("thrust", self.throttle, gain * tg)

    def delta_roll_relative(self, gain):
        self._update_input("roll", self.aileron, gain * ag)

    def delta_pitch_relative(self, gain):
        self._update_input("pitch", self.elevator, gain * eg)

    def delta_yaw_relative(self, gain):
        self._update_input("yaw", self.rudder, gain * rg)

    def roll(self, roll):
        """
        @:param roll: between -1 and 1
        """
        self.aileron = self._get_mapped_value(roll)

    def pitch(self, pitch):
        self.elevator = self._get_mapped_value(pitch)

    def yaw(self, yaw):
        self.rudder = self._get_mapped_value(yaw)

    def thrust(self, throttle):
        self.throttle = self._get_mapped_value(throttle)

    def reset_inputs(self):
        self.throttle = INPUT_MIN
        self.aileron = INPUT_MID
        self.rudder = INPUT_MID
        self.elevator = INPUT_MID

    def max_throttle(self):
        self.throttle = INPUT_MAX

    def go_throttle(self):
        self.throttle = INPUT_MAX
        self.send_command()
        self.throttle = THROTTLE_GO
        self.send_command()

    def level_throttle(self):
        self.throttle = INPUT_MID

    def reset_rotation(self):
        self.aileron = INPUT_MID
        self.rudder = INPUT_MID
        self.elevator = INPUT_MID

    def send_command(self):
        command = "%i, %i, %i, %i" % (self.throttle, self.aileron, self.elevator, self.rudder)
        self.arduino.write(str.encode(command + "\n"))
        return command

    def values(self):
        return 'T: %f R:%f P:%f Y:%f' % (self.throttle, self.aileron, self.elevator, self.rudder)

    def init_throttle(self):
        self.max_throttle()
        cmd = self.send_command()
        print("\nCommand sent: ")
        print("Thr, Roll, Pitch, Yaw:")
        print(cmd)

        time.sleep(0.5)
        self.go_throttle()
        cmd = self.send_command()
        print("\nCommand sent: ")
        print("Thr, Roll, Pitch, Yaw:")
        print(cmd)

        time.sleep(0.5)
