import serial
from threading import Thread
from time import time, sleep
import sys
# import main_gui

class Printer:
    def __init__(self, descriptive_device_name, port_name, baudrate):
        # Communication inputs
        self.descriptive_device_name = descriptive_device_name
        self.port_name = port_name
        self.baudrate = baudrate

        # Communication
        self._raw_received_message = None
        self.printer = None
        self._ok_flag = False

        # Other
        self.home_pos = [0,0,0]
        self._finish = False

    def _serial_readline(self):
        while True:
            try:
                self._raw_received_message = self.printer.readline().decode('utf-8')[:-1]
                if self._raw_received_message == "ok":
                    self._ok_flag = True
                if self._raw_received_message[:1] == "X":
                    self._finish = True
            except:
                pass
            sleep(0.001)

    def _start_Reading_Thread(self):
        self.__thread = Thread(target=self._serial_readline)
        self.__thread.daemon = True
        self.__thread.start()

    def connect(self, timeout = 20):
        try: 
            self.printer = serial.Serial(port=self.port_name, baudrate=self.baudrate)
            print("Successfully connected to " + self.descriptive_device_name)
        except:
            print("!! Cannot connect to " + self.descriptive_device_name + " !!")
            # sys.exit()
            return False

        self._start_Reading_Thread()

        print("Waiting until printer initializes")
        timer = time()
        while True:
            if self._raw_received_message == "echo:SD init fail":
                print("Successfully initialized " + self.descriptive_device_name)
                break

            if time() - timer > timeout:
                print("!! " +  self.descriptive_device_name + " init failed !!")
                # sys.exit()
                return False

                # print("Starting in Offline Mode")
                # print("The debug variable was", main_gui.debug)
                # main_gui.debug = True
                # print("The debug variable is set to", main_gui.debug)
                # break

        return True

    def disconnect(self):
        try: 
            self.printer.close()
            print("Disconnected " + self.descriptive_device_name)
        except:
            print("!! Cannot disconnect " + self.descriptive_device_name + " !!")
            sys.exit()

    def _send_msg(self, msg):
        self.printer.write(str.encode(msg)) 

    def send_gcode(self, gcode, wait_until_completion = True, printMsg = True):
        self._ok_flag = False
        self._send_msg(gcode + "\r\n")

        if wait_until_completion:
            while True:
                if self._ok_flag: 
                    break
            if printMsg:
                print("Process complete: ", gcode)

    def max_x_feedrate(self, speed):
        self.send_gcode("M203 X" + str(float(speed)), printMsg=False)

    def max_y_feedrate(self, speed):
        self.send_gcode("M203 Y" + str(float(speed)), printMsg=False)
        
    def max_z_feedrate(self, speed):
        self.send_gcode("M203 Z" + str(float(speed)), printMsg=False)

    def stop_motion(self):
        self.send_gcode("M410", printMsg=False)

    def set_home_pos(self, x = 0, y = 0, z = 0):
        self.home_pos = [x, y, z]

    def homing(self, printMsg=False):
        self.send_gcode("G28 R25", printMsg=printMsg)

    def move_home(self, f = 1000, printMsg=False):
        self.move_axis(x = self.home_pos[0], y = self.home_pos[1], z = self.home_pos[2], f = f, printMsg=printMsg)

    def move_axis_relative(self, x = None, y = None, z = None, e = None, f = None, printMsg = False, offset = None):
        self._finish = False
        if offset is None:
            offset = [0, 0, 0]
            
        offset[0] = offset[0] + self.home_pos[0]
        offset[1] = offset[1] + self.home_pos[1]
        offset[2] = offset[2] + self.home_pos[2]
        command = "G0"
        
        if x is not None:
            command = command + " X" + str(x + offset[0])
        if y is not None:
            command = command + " Y" + str(y + offset[1])
        if z is not None:
            command = command + " Z" + str(z + offset[2])
        if e is not None:
            command = command + " E" + str(e)
        if f is not None:
            command = command + " F" + str(float(100*f))

        self.send_gcode(command, wait_until_completion=True, printMsg=printMsg)

    def move_axis(self, x = None, y = None, z = None, e = None, f = None, printMsg = False, offset=None):
        self._finish = False
        if offset is None:
            offset = [0, 0, 0]
            
        offset[0] = offset[0] + self.home_pos[0]
        offset[1] = offset[1] + self.home_pos[1]
        offset[2] = offset[2] + self.home_pos[2]
        
        command = "G0"
        
        if x is not None:
            command = command + " X" + str(x)
        if y is not None:
            command = command + " Y" + str(y)
        if z is not None:
            command = command + " Z" + str(z)
        if e is not None:
            command = command + " E" + str(e)
        if f is not None:
            command = command + " F" + str(float(100*f))

        self.send_gcode(command, wait_until_completion=False, printMsg=printMsg)

    def move_axis_incremental(self, x = None, y = None, z = None, e = None, f = None, printMsg = False):
        self._finish = False
        command = "G0"
        position = self.read_position(printMsg=False)
        
        if x is not None:
            command = command + " X" + str(x + position[0])
        if y is not None:
            command = command + " Y" + str(y + position[1])
        if z is not None:
            command = command + " Z" + str(z + position[2])
        if e is not None:
            command = command + " E" + str(e)
        if f is not None:
            command = command + " F" + str(float(100*f))

        self.send_gcode(command, wait_until_completion=True, printMsg=printMsg)
        
    def set_position(self, x = None, y = None, z = None, e = None, f = None, printMsg = False):
        self._finish = False
        command = "G92"
        if x is not None:
            command = command + " X" + str(x)
        if y is not None:
            command = command + " Y" + str(y)
        if z is not None:
            command = command + " Z" + str(z)
            
        self.send_gcode(command, wait_until_completion=False, printMsg=printMsg)

    def read_position(self, printMsg=False):
        while True: 
            try:
                self.send_gcode("M114", wait_until_completion=False, printMsg=printMsg)

                pos = None
                while True:
                    if self._raw_received_message[:1] == "X" and pos is None:
                        pos = self._raw_received_message

                    if self._ok_flag: 
                        break
                
                if printMsg:
                    print("position:", pos)

                msg = pos.split(":")

                position = []
                for i, m in enumerate(msg):
                    if i > 0 and i < 4:
                        position.append(float(m[:-2]))

                return position
            except:
                print('read position error')
                sleep(0.2)
                
                
    def read_position_relative(self, printMsg=False):
        pos = self.read_position()
        pos[0] = pos[0] + self.home_pos[0]
        pos[1] = pos[1] + self.home_pos[1]
        pos[2] = pos[2] + self.home_pos[2]
        
        if printMsg:
            print("position:", pos)
        return pos
    
            
    def finish_request(self, printMsg = False):
        
        self._finish = False     
        self.send_gcode("M114", wait_until_completion=False, printMsg=printMsg)
        
    def get_ok_flag(self):
        return self._ok_flag
    
    def get_finish_flag(self):
        return self._finish
    
    def change_idle_time(self, time = 120):
        self.send_gcode("M84 S" + str(time), printMsg=False)
    
    def disable_axis(self, x = False, y = False, z = False, all = False):
        command = "M18"
        if x or all:
            command = command + " X"
        if y or all:
            command = command + " Y"
        if z or all:
            command = command + " Z"
            
        self.send_gcode(command, printMsg=False)
                        
        
class position:
    def __init__(self, x=None, y=None, z=None, e=None, f=None):
        self.x = x
        self.y = y
        self.z = z
        self.e = e  
        self.f = f
