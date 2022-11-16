# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////

import math
import sys
import time
import threading

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO 
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus


# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
ON = False
OFF = True
HOME = True
TOP = False
OPEN = False
CLOSE = True
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
DEBOUNCE = 0.1
INIT_RAMP_SPEED = 2
RAMP_LENGTH = 725


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):
    def build(self):
        self.title = "Perpetual Motion"
        return sm

Builder.load_file('main.kv')
Window.clearcolor = (.1, .1,.1, 1) # (WHITE)

cyprus.open_spi()
cyprus.initialize()
cyprus.setup_servo(2)

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////
sm = ScreenManager()
ramp = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
             steps_per_unit=200, speed=INIT_RAMP_SPEED)

# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
	
# ////////////////////////////////////////////////////////////////
# //        DEFINE MAINSCREEN CLASS THAT KIVY RECOGNIZES        //
# //                                                            //
# //   KIVY UI CAN INTERACT DIRECTLY W/ THE FUNCTIONS DEFINED   //
# //     CORRESPONDS TO BUTTON/SLIDER/WIDGET "on_release"       //
# //                                                            //
# //   SHOULD REFERENCE MAIN FUNCTIONS WITHIN THESE FUNCTIONS   //
# //      SHOULD NOT INTERACT DIRECTLY WITH THE HARDWARE        //
# ////////////////////////////////////////////////////////////////
class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    staircaseSpeedText = '0'
    rampSpeed = INIT_RAMP_SPEED
    staircaseSpeed = 40

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()

    def toggleGate(self):
        if self.ids.gate.mDir == 0:
            cyprus.set_servo_position(2, 0.7)
            self.ids.gate.mDir = 1
        elif self.ids.gate.mDir == 1:
            cyprus.set_servo_position(2, 0.25)
            self.ids.gate.mDir = 0


    def toggleStaircase(self):
        if self.ids.staircase.lDir == 1:
            print("off")
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.ids.staircase.lDir = 0
        elif self.ids.staircase.lDir == 0:
            print("on")
            cyprus.set_pwm_values(1, period_value=100000, compare_value=self.ids.staircase.value,
                                  compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            self.ids.staircase.lDir = 1

        
    def toggleRamp(self):
        print("Move ramp up and down here")
        if not (cyprus.read_gpio() & 0b0010):
            while (cyprus.read_gpio() & 0b0001):
                ramp.run(0, self.ids.ramp.value)
                print(self.ids.ramp.value)
            if not (cyprus.read_gpio() & 0b0001):
                ramp.go_until_press(1, 55000)
        
    def auto(self):
        print("Run through one cycle of the perpetual motion machine")
        self.toggleRamp()
        sleep(7)
        self.toggleStaircase()
        sleep(7)
        self.toggleStaircase()
        sleep(3)
        self.toggleGate()
        sleep(3)
        self.toggleGate()


        
    def setRampSpeed(self, speed):
        x = str(speed)
        self.ids.rampSpeedLabel.text = str('Ramp Speed: ' + x)
        ramp.set_speed(speed)
        self.ids.ramp.value = int(ramp.speed) / 50
        print(self.ids.ramp.value)
        
    def setStaircaseSpeed(self, speed):
        self.staircaseSpeed = str(speed)
        x = int(self.staircaseSpeed) * 1000
        print(x)
        self.ids.staircase.value = x
        print(self.ids.staircase.value)
        self.ids.staircaseSpeedLabel.text = str('Staircase Speed: ' + self.staircaseSpeed)
        
    def initialize(self):
        print("Close gate, stop staircase and home ramp here")
        cyprus.set_servo_position(2, 0)

    def resetColors(self):
        self.ids.gate.color = YELLOW
        self.ids.staircase.color = YELLOW
        self.ids.ramp.color = YELLOW
        self.ids.auto.color = BLUE
    
    def quit(self):
        print("Exit")
        MyApp().stop()

sm.add_widget(MainScreen(name = 'main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
