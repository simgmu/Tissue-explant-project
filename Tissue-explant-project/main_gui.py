import tkinter as tk                     
from tkinter import ttk 
import json
import customtkinter as ctk
import numpy as np
import math
import os
import time as tm
from loguru import logger
import threading
import queue
    
from Platform.Communication.ports_gestion import * 
import Platform.computer_vision as cv
from PIL import Image, ImageTk
import Developpement.Cam_gear as cam_gear
import cv2

import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="customtkinter") 


debug = False
skip_calibration = False
gel_prep = True
cam_check = True
manual_first_check = False

mask_size = 150 # it actually should be 200 but the petri-dish borders are annoying for picks

print_log = True
print_all = False 
print_pipette_state = False

if debug:
    from Platform.Communication.fake_communication import * 
else:
    from Platform.Communication.dynamixel_controller import *
    from Platform.Communication.printer_communications import * 
    import Developpement.Cam_gear as cam_gear


import importlib
    

### ATTENTION AU OFFSET  !!!
SETTINGS = "settings.json"
X_MIN = -9.0
# X_MAX = 183.0 # Why was this so low?
X_MAX = 190.0
Y_MIN = 0.0
#Y_MAX = 145.0 # Why was this so low? 
Y_MAX = 220.0
Z_MIN = 0.0
Z_MAX = 180.0

DEFAULT_MODE = "System"
ctk.set_appearance_mode(DEFAULT_MODE)  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

DARK_COLOR = "#242424"
LIGHT_COLOR = "#ebebeb"

DEFAULT_LIGHT = "#dbdbdb"
DEFAULT_DARK = "#2b2b2b"


#################################################################################################################################
#                                                           GUI elements                                                        #
#################################################################################################################################



class ArrowButtonRight(tk.Frame):  ## replace these with pictures
    def __init__(self, master=None, size=40, target_class=None, printer_class=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        
        self.target_class = target_class
        self.printer_class = printer_class
        self.canvas = tk.Canvas(self, width=size, height=size)
        self.canvas.create_polygon(7, 7, 35, 20, 7, 33, fill="black", outline="black")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.grid()
        self.other_class = None
        
    def assign_class(self, other_class):
        self.other_class = other_class

    def on_click(self, event):
        if self.target_class.is_homed:
            if print_all: print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in X-UP")
            self.target_class.move_xyz(x=self.target_class.xyz_step_buttons.get(), y=0, z=0)
        else:
            if print_log: logger.info(" Printer not homed yet, please home the printer first")
            if print_all: print(" Printer not homed yet, please home the printer first")


class ArrowButtonTop(tk.Frame):
    def __init__(self, master=None, size=40, target_class=None, is_z = False, printer_class=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        
        self.target_class = target_class
        self.printer_class = printer_class
        self.is_z = is_z
        self.canvas = tk.Canvas(self, width=size, height=size)
        self.canvas.create_polygon(7, 33, 20, 7, 33, 33, fill="black", outline="black")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.pack()

    def on_click(self, event):
        
        if self.target_class.is_homed:
            if self.is_z:
                if print_all: print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Z-UP")
                self.target_class.move_xyz(x=0, y=0, z=self.target_class.xyz_step_buttons.get())
            else:
                if print_all: print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Y-UP")
                self.target_class.move_xyz(x=0, y=self.target_class.xyz_step_buttons.get(), z=0)
        else:
            if print_all: print(" Printer not homed yet, please home the printer first")
            

class ArrowButtonLeft(tk.Frame):
    def __init__(self, master=None, size=40, target_class=None, printer_class=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)
        
        self.target_class = target_class
        self.printer_class = printer_class
        self.canvas = tk.Canvas(self, width=size, height=size)
        self.canvas.create_polygon(7, 20, 35, 7, 35, 33, fill="black", outline="black")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.pack()

    def on_click(self, event):
        if self.target_class.is_homed:
            if print_all: print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in X-DOWN")
            self.target_class.move_xyz(x=-self.target_class.xyz_step_buttons.get(), y=0, z=0)
        else:
            if print_all: print(" Printer not homed yet, please home the printer first")


class ArrowButtonBottom(tk.Frame):
    def __init__(self, master=None, size=40, target_class=None, is_z = False, printer_class=None, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        self.target_class = target_class
        self.printer_class = printer_class
        self.is_z = is_z
        self.canvas = tk.Canvas(self, width=size, height=size)
        self.canvas.create_polygon(7, 7, 20, 33, 33, 7, fill="black", outline="black")
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.pack()

    def on_click(self, event):
        if self.target_class.is_homed:
            if self.is_z:
                if print_all: print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Z-DOWN")
                self.target_class.move_xyz(x=0, y=0, z=-self.target_class.xyz_step_buttons.get())
            else:
                if print_all: print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Y-DOWN")
                self.target_class.move_xyz(x=0, y=-self.target_class.xyz_step_buttons.get(), z=0)
        else:
            if print_all: print(" Printer not homed yet, please home the printer first")
            

class RoundButton(tk.Canvas):
    def __init__(self, master=None, diameter=50, bg_color="lightgray", target_class=None, printer_class=None, **kwargs):
        tk.Canvas.__init__(self, master, width=diameter, height=diameter, bg=bg_color, highlightthickness=0, **kwargs)
        self.diameter = diameter

        self.target_class = target_class
        self.printer_class = printer_class
        # Draw a circle on the canvas
        radius = diameter // 2
        self.create_oval(0, 0, diameter, diameter, outline="black", fill=bg_color)

        self.bind("<Button-1>", self.on_click)

    def on_click(self, event):
        if print_all: print("home position")
        self.target_class.move_home()
        
        
class MyWindow(ctk.CTk):
    def __init__(self): 
        super().__init__()
        self.create_variables()
        if debug:
            self.title("X-Plant control panel - Debug mode")
        else:
            self.title("X-Plant control panel")
        self.geometry("1200x750")
        self.protocol("WM_DELETE_WINDOW", self.close_window)

        if debug:
            self.title_ = ctk.CTkLabel(self, text="X-plant - Debug mode", font=("Arial Bold", 18))
        else:
            self.title_ = ctk.CTkLabel(self, text="X-plant", font=("Arial Bold", 18))
        self.title_.grid(pady=10)

        self.gui_mode_frame = ctk.CTkFrame(self)
        self.gui_mode_frame.grid(row=2, column=0, padx=10, pady=15)
        self.gui_mode = ctk.CTkLabel(self.gui_mode_frame, text="GUI mode", font=("Arial Bold", 18))
        self.gui_mode.grid(row=0, column=0, padx=10, pady=10)
        self.gui_mode_menu = ctk.CTkOptionMenu(self.gui_mode_frame,
                                               values=["Light", "Dark", "System"],
                                               command=self.change_appearance_mode_event)
        self.gui_mode_menu.grid(row=0, column=1, padx=20, pady=10)
        self.gui_mode_menu.set(DEFAULT_MODE)
        
        self.tabControl = ctk.CTkTabview(self, height=250)

        for i in range(len(self.tabs_name)):
            self.tab.append(ctk.CTkFrame(self.tabControl))
            self.tabControl.add(self.tabs_name[i])
            self.set_tabs(i)
        self.tabControl._segmented_button.configure(font=("Arial Bold", 15))
        self.tabControl.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.columnconfigure(0, minsize=400, weight=1)
        self.rowconfigure(1, minsize=400,weight=1)
        
        self.tabControl.set(self.tabs_name[4])
        self.isOpen = True


    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)
        if self.isOpen:
            self.update_parameters()
    
    
    def create_variables(self):
       
        self.is_homed = False
        self.tip_calibration_done = False
        self.manual_mode = True
        self.tissue_placed = True
        self.auto_check = False
        self.reference = None
        self.current_mixing_tube = 1

        self.load_parameters()
        self.tab        = []
        self.tabControl = None
        
        self.tabs_name      = ["Mode", "Cameras", "Parameters", "Well plate", 
                               "Motion Control", "Documentation"] 
        
        self.camera_displayed_text = tk.StringVar()
        self.displayed_cameras = 1
        self.camera_displayed_text.set("Camera "+str(self.displayed_cameras))
        self.frames         = [[],[]]
        self.camera_feed    = [[None, None, None],
                               [None]]
        self.camera_button_text = [None, None]
        self.create_well_variables()
        self.create_motion_variables()
        self.connect_printer_dynamixel()
        
    
    def load_parameters(self):
        with open(SETTINGS, 'r') as f:
            self.settings = json.load(f)
            
            
    def create_well_variables(self):
        # You can add any plates you want here, by defining the name in self.options and its layout in self.layout
        self.options        = ["TPP6", "Millicell plate", "TPP12", "TPP24", "TPP48", "NUNC48", "FALCON48"]
        self.label_col      = ["A", "B", "C", "D", "E", "F"]
        self.label_row      = ["1", "2", "3", "4", "5", "6", "7", "8"]
        self.layout         = [[2,3], # TPP6
                               [2,3], # Millicell
                               [3,4], # TPP12
                               [4,6], # TPP24
                               [6,8], # TPP48
                               [6,8], # NUNC48
                               [6,8]] # FALCON48
        self.selected_wells = []

        # Couple of adds
        # self.debug = debug
        self.well_num = 0
        self.well_nb_with_gel = 0
        self.nb_sample = 0
        # self.nb_samples_per_well = 0
        self.gel_preparation = False
        
        self.petridish_pos = [64, 131]
        self.petridish_radius = 45
        # self.tip_pos_px = [396, 736] # Is recalibrated during Tip calibration
        self.tip_pos_px = self.settings["Offset"]["Tip pixel position"]
        # self.tip_pos_px = [160 + 396.33953772 + 5, 430 - 736.22499283 - 5]


        # self.pipette_1_pos = 0
        # self.pipette_2_pos = 0
        # Those two values are discontinued

        # if print_pipette_state: 
            # print("Pipette 1 position: ", self.pipette_1_pos, "Pipette 2 position: ", self.pipette_2_pos)
            # print("Servo 1 position: ", self.servo_pos[0], "Servo 2 position: ", self.servo_pos[1])

        self.x_firmware_limit_overwrite = -11 # Was at -9 but second pipette + camera wouldn't work 

        self.well_dim_x     = 300
        self.well_dim_y     = 480
        self.well_menu           = None
        
        self.well_plate_grid    = None
        self.well_buttons       = []
        
        self.text_well_plate_explanation = ''' Here, you can select the well plate you want to use. It will display a simulation of the grid,
in which you can select UP TO 6 wells to use. You can then press the save button to save the selected wells into the config file.'''.replace('\n', ' ' )
        self.tab_well_explanation   = None    
        self.tab_well_results       = None
        self.text_well_results      = None
        self.remaining_wells        = None
        self.text_remaining_wells   = None
        self.well_button_grid       = None
        self.well_reset_button      = None
        self.well_save_button       = None

        self.target_pos = None
        
                
    def create_motion_variables(self):
        self.button_bottom  = None
        self.button_top     = None
        self.button_left    = None
        self.button_right   = None
                
        self.z_button_up    = None
        self.z_button_down  = None
        
        
        # self.safe_height        = 55
        # In regards to the tubes and vial heights, this safe height is much safer:
        self.safe_height        = 70
        
        self.offset             = [0, 0, 0]
        self.coord_label        = []
        self.coord_value        = []
        self.coord_value_text   = []
        self.last_pos           = [0, 0, 0]
        
        self.servo_buttons      = []
        self.servo_frame        = []
        self.servo_labels       = []
        self.servo_values       = []
        self.servo_values_text  = []
        self.unit_list          = ["steps", "percentage", "μl"] 
        self.is_unit_percentage = False
        self.servo_step_buttons = []
        self.servo_pos          = []
        
        self.servo_names        = ["Servo pipette 1", "Servo pipette 2", "Servo speed"]
        self.toolhead_position  = ["Neutral", "Tip one", "Tip two"]
        
        
        self.tip_number     = 0
        self.pipette_empty  = 570 # this variable shouldn't exists! We should calibrate with the value inside write_pipette_ul
        self.pipette_max_ul = 680 # ONLY FOR PURGING
        self.servo_pos      = [self.pipette_empty, self.pipette_empty, 30]
        
        self.buffer_moves = []


#################################################################################################################################
#                                                   Connection/ Initialisation                                                  #
#################################################################################################################################
                
                
    def connect_printer_dynamixel(self):
        self.anycubic = Printer(descriptive_device_name="printer", 
                                port_name=get_com_port("1A86", "7523"), 
                                baudrate=115200)
        
        self.dynamixel = Dynamixel(ID=[1,2,3], 
                                   descriptive_device_name="XL430 test motor", 
                                   series_name=["xl", "xl", "xl"], 
                                   baudrate=57600,
                                   pipette_max_ul = self.pipette_max_ul,
                                   pipette_empty=self.pipette_empty,    
                                   port_name=get_com_port("0403", "6014"))
        
        global debug
        if print_all: print("Launching with debug mode: ", debug)
        connection_success = self.anycubic.connect()
        if connection_success == False:
            debug = True
        if print_all: print("After trying to connect, debug mode: ", debug)

        if debug:
            module = importlib.import_module('Platform.Communication.fake_communication')
            globals().update(vars(module))
            import Platform.Communication.fake_communication
            self.anycubic = Printer(descriptive_device_name="printer", 
                                port_name=get_com_port("1A86", "7523"), 
                                baudrate=115200)
        
            self.dynamixel = Dynamixel(ID=[1,2,3], 
                                    descriptive_device_name="XL430 test motor", 
                                    series_name=["xl", "xl", "xl"], 
                                    baudrate=57600,
                                    pipette_max_ul = self.pipette_max_ul,
                                    pipette_empty=self.pipette_empty,    
                                    port_name=get_com_port("0403", "6014"))
            self.anycubic.connect()

        if debug == False:
            self.anycubic.change_idle_time(time = 300)
        
        self.dynamixel.begin_communication()  
        self.dynamixel.set_operating_mode("position", ID="all")
        self.dynamixel.write_profile_velocity(100, ID="all")
        self.dynamixel.set_position_gains(P_gain = 2700, I_gain = 50, D_gain = 5000, ID=1)
        self.dynamixel.set_position_gains(P_gain = 2700, I_gain = 90, D_gain = 5000, ID=2)
        self.dynamixel.set_position_gains(P_gain = 2500, I_gain = 40, D_gain = 5000, ID=3)
        # self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
        if debug == False:
            self.tip_number = self.dynamixel.read_tip()
            if self.tip_number == False:
                self.tip_number = 1
                self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
            
            

            pos = [*self.dynamixel.read_pos_in_ul(ID=[1,2]),30]
            pos[0] = round(pos[0],0)
            pos[1] = round(pos[1],0)
            self.servo_pos = pos
        else:
            self.tip_number = 0
            self.servo_pos = [self.pipette_empty, self.pipette_empty, 30]
        # self.dynamixel.write_pipette_ul(self.pipette_empty, ID=[1,2])
        self.dynamixel.write_profile_velocity(self.servo_pos[-1], ID=[1,2])
        
        self.purging = False
        
            
    def set_tabs(self, i):
        if i == self.tabs_name.index("Mode"):
            self.set_tab_mode()
        elif i == self.tabs_name.index("Cameras"):
            self.set_tab_cameras()
        elif i == self.tabs_name.index("Parameters"):
            self.set_tab_parameters()
        elif i == self.tabs_name.index("Well plate"):
            self.set_tab_well_plate()
        elif i == self.tabs_name.index("Motion Control"):
            self.set_tab_motion_control()
        elif i == self.tabs_name.index("Documentation"):
            self.set_tab_documentation()
            
                  
    def debug_function(self):
        if print_all: print("test")
        
#################################################################################################################################
#                                                  Tabs and their specifications                                                #
#################################################################################################################################

    #### Functions related to the mode tab ####            
    def set_tab_mode(self):
        self.mode_control_frame = ctk.CTkFrame(self.tabControl.tab("Mode"))
        self.mode_control_frame.place(relx=0.1, rely=0)
        self.calibration_buttons()
        self.step_buttons()

        # Message text box
        self.message_box = ctk.CTkTextbox(self.tabControl.tab("Mode"), width=500, height=30)
        self.message_box.place(relx=0.1, rely=0.9)
        # self.message_box.grid(row=2, columnspan=2)
        
        self.camera_mode_frame = ctk.CTkFrame(self.tabControl.tab("Mode"))
        # self.camera_mode_frame.place(relx=0.8, rely=0.65, anchor=tk.CENTER)
        self.camera_mode_frame.place(relx=0.6, rely=0)

        self.mode_camera_button = ctk.CTkButton(self.camera_mode_frame, 
                                             textvariable=self.camera_displayed_text,
                                             command= self.show_camera_control)
        self.mode_camera_button.grid(row=6)
        
        self.camera_feed_mode = ctk.CTkLabel(self.camera_mode_frame, text = "", width=480, height=270)
        self.camera_feed_mode.grid(row=7)  

        # Toggle button 1
        self.auto_check_toggle_1 = ctk.CTkSwitch(self.camera_mode_frame, text="Automatic Check 1",
                                                command=self.toggle_auto_check_1,
                                                onvalue=True, offvalue=False)
        self.auto_check_toggle_1.grid(row=2)
        # Initially set to True
        self.auto_check_toggle_1.toggle()

        # Toggle button 2
        self.cam_check = ctk.CTkSwitch(self.camera_mode_frame, text="Include Check 2", 
                                                command=self.toggle_cam_check,
                                                onvalue=True, offvalue=False)
        # self.auto_check_toggle.grid(row=4, column=0, columnspan=2, pady=10)  # Adjust grid placement as needed
        # The toggle button should be above the camera feed (upper right corner)
        self.cam_check.grid(row=3)
        # Initially set to True
        self.cam_check.toggle()


        # Toggle button 3
        self.auto_check_toggle_2 = ctk.CTkSwitch(self.camera_mode_frame, text="Automatic Check 2", 
                                                command=self.toggle_auto_check,
                                                onvalue=True, offvalue=False)
        # self.auto_check_toggle.grid(row=4, column=0, columnspan=2, pady=10)  # Adjust grid placement as needed
        # The toggle button should be above the camera feed (upper right corner)
        self.auto_check_toggle_2.grid(row=4)

        # Toggle button 4
        self.gel_prep_toggle = ctk.CTkSwitch(self.camera_mode_frame, text="Include Gel in Run All",
                                                command=self.gel_prep_toggle,
                                                onvalue=True, offvalue=False)
        self.gel_prep_toggle.grid(row=5)
        # Initially set to True
        self.gel_prep_toggle.toggle()



        # Stopwatch
        # title("Stopwatch")

        # Timer label
        self.timer_label = tk.Label(self.camera_mode_frame, text="00:00:00", font=("Arial", 30))
        # self.timer_label.pack(pady=20)
        self.timer_label.grid(row=0)

        # # Button to simulate finishing the mixing process
        # start_button = tk.Button(root, text="Finish Mixing", command=start_stopwatch)
        # start_button.pack(pady=20)

        self.stop_button = ctk.CTkButton(self.camera_mode_frame, text="Stop", command=self.stop_stopwatch)
        self.stop_button.grid(row=1, pady=20)  # Place the button below the timer

        self.running = False
        self.start_time = None
        self.update_queue = queue.Queue()
        # Start the GUI loop
        # root.mainloop()
        self.after(100, self.process_queue)


    def start_stopwatch(self):
        self.running = True
        self.start_time = tm.time()
        threading.Thread(target=self.update_timer).start()
        # self.update_timer()

    def update_timer(self):
        while self.running:
            elapsed_time = tm.time() - self.start_time
            formatted_time = self.format_time(elapsed_time)
            # self.timer_label.configure(text=formatted_time)
            # tm.sleep(0.1)  # Update every 100 ms
            # self.after(100, self.update_timer)

            # self.after(0, self.timer_label.config, {"text": formatted_time})
            # tm.sleep(0.1)

            self.update_queue.put(formatted_time)
            tm.sleep(0.1)

    
    def process_queue(self):
        while not self.update_queue.empty():
            formatted_time = self.update_queue.get()
            self.timer_label.config(text=formatted_time)
        self.after(100, self.process_queue)  # Keep checking the queue


    def format_time(self, seconds):
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    def stop_stopwatch(self):
        self.running = False
        if print_all: print("Stopwatch stopped at ", self.timer_label.cget("text"))
        if print_log: logger.info("Stopwatch stopped at ", self.timer_label.cget("text"))


    def toggle_cam_check(self):
        global cam_check
        cam_check = self.cam_check.get()
        if print_all: print("Camera check included: ", cam_check)
        if print_log: logger.info("Camera check included: ", cam_check)
        
    def gel_prep_toggle(self):
        global gel_prep
        gel_prep = self.gel_prep_toggle.get()
        if print_all: print("Gel preparation included: ", gel_prep)

    def toggle_auto_check_1(self):
        # Inverse of the current state of the toggle is the manual_first_check
        global manual_first_check
        if self.auto_check_toggle_1.get():
            manual_first_check = False
        else:
            manual_first_check = True
        if print_all: print("Manual first check: ", manual_first_check)


    def toggle_auto_check(self):
        self.auto_check = self.auto_check_toggle_2.get()  # Current state of the toggle
        if self.auto_check:
            if print_all: print("Switching to Automatic Check")
        else:
            if print_all: print("Switching to Manual Check")
        
    def calibration_buttons(self):
        
        self.calibration_frame = ctk.CTkFrame(self.mode_control_frame)
        self.calibration_frame.grid(row = 0, column = 0, padx = 10)
        
        self.calibration_label = ctk.CTkLabel(self.calibration_frame, text="Calibrations:")
        self.calibration_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.full_calibration_button = ctk.CTkButton(self.calibration_frame, text="Full Calibration", command=self.fullcalibration)  
        self.full_calibration_button.grid(row=1, column=0, padx=10, pady=10)
        
        self.calibrate_offset_button = ctk.CTkButton(self.calibration_frame, text="Calibrate Tips", command=self.offsetcalibration) 
        self.calibrate_offset_button.grid(row=2, column=0, padx=10, pady=10)
        
        self.calibrate_offset_button = ctk.CTkButton(self.calibration_frame, text="Calibrate Tubes", command=self.tubecalibration) 
        self.calibrate_offset_button.grid(row=3, column=0, padx=10, pady=10)

        self.xyz_homing_button = ctk.CTkButton(self.calibration_frame, text="XYZ Homing", command=self.move_home)
        self.xyz_homing_button.grid(row=4, column=0, padx=10, pady=10)

        self.take_picture_button = ctk.CTkButton(self.calibration_frame, text="Fixed Camera", command=self.take_picture) 
        self.take_picture_button.grid(row=5, column=0, padx=10, pady=10)

        self.take_picture_button = ctk.CTkButton(self.calibration_frame, text="Empty Pipette", command=self.empty_out) 
        self.take_picture_button.grid(row=6, column=0, padx=10, pady=10)

        self.take_picture_button = ctk.CTkButton(self.calibration_frame, text="Remove Tip-bubble", command=self.remove_bubble) 
        self.take_picture_button.grid(row=7, column=0, padx=10, pady=10)
        
    
    def step_buttons(self):
        self.steps_frame = ctk.CTkFrame(self.mode_control_frame)
        self.steps_frame.grid(row = 0, column = 1, padx = 10)
        
        self.steps_label = ctk.CTkLabel(self.steps_frame, text="Steps:")
        self.steps_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.run_all_button = ctk.CTkButton(self.steps_frame, text="Run All", command=self.run_all)
        self.run_all_button.grid(row=1, column=0, padx=10, pady=10)
        
        self.prep_gel_button = ctk.CTkButton(self.steps_frame, text="Prepare Gel", command=self.prepare_gel)
        self.prep_gel_button.grid(row=2, column=0, padx=10, pady=10)

        self.prep_gel_button = ctk.CTkButton(self.steps_frame, text="Apply Gel", command=self.apply_gel)
        self.prep_gel_button.grid(row=3, column=0, padx=10, pady=10)

        self.detect_button = ctk.CTkButton(self.steps_frame, text="Detect", command=self.detect)
        self.detect_button.grid(row=4, column=0, padx=10, pady=10)
        
        self.pick_button = ctk.CTkButton(self.steps_frame, text="Pick", command=self.pick)
        self.pick_button.grid(row=5, column=0, padx=10, pady=10)

        self.pnp_button = ctk.CTkButton(self.steps_frame, text="Place", command=self.place)
        self.pnp_button.grid(row=6, column=0, padx=10, pady=10)

        self.pnp_button = ctk.CTkButton(self.steps_frame, text="Pick and Place", command=self.pick_and_place)
        self.pnp_button.grid(row=7, column=0, padx=10, pady=10)
    
    #### Functions related to the camera tab ####
    def set_tab_cameras(self):
        
        ## find how to increase image size according to label size
        self.camera_feed_camera_0 = ctk.CTkLabel(self.tabControl.tab("Cameras"), text="", width=640, height=360)
        self.camera_feed_camera_0.place(relx=0.1, rely=0.2)
        self.camera_feed_camera_1 = ctk.CTkLabel(self.tabControl.tab("Cameras"), text="", width=640, height=360)
        self.camera_feed_camera_1.place(relx=0.6, rely=0.2)
        
        if debug == False:
            self.stream1 = cam_gear.camThread("Camera 1", get_cam_index("TV Camera")) 
            self.stream1.start()
            frame = cam_gear.get_cam_frame(self.stream1)  
            self.cam = cv.Camera(frame)
            self.frame = self.cam.undistort(frame)
            if print_all: print("the frame shape initially is :", self.frame.shape)
            self.invert = cv.invert(self.frame)

            # self.mask = cv.create_mask(200, self.frame.shape[0:2], (self.frame.shape[1]//2, self.frame.shape[0]//2))
            self.mask = cv.create_mask(mask_size, self.frame.shape[0:2], (self.frame.shape[1]//2, self.frame.shape[0]//2))

            self.intruder_detector = cv.create_intruder_detector()
            self.min_radius = 15
            self.max_radius = 38
            self.detect_attempt = 0
            self.pick_attempt = 0
            self.max_detect_attempt = self.settings["Detection"]["Max attempts"]
            
            # Camera 2 - Macro Camera
            self.stream2 = cam_gear.camThread("Camera 2", get_cam_index("USB2.0 UVC PC Camera"))
        else:
            self.stream1 = cv2.imread("Pictures/cam2/failed_capture_0.png")
            self.stream2 = cam_gear.camThread("Camera 2", 0) # laptop camera
           
            self.min_radius = 15
            self.max_radius = 38
            self.detect_attempt = 0
            self.pick_attempt = 0
            self.max_detect_attempt = self.settings["Detection"]["Max attempts"]        
        self.stream2.start()
        self.macro_frame = cam_gear.get_cam_frame(self.stream2)
        self.picture_pos = -self.settings["Offset"]["Tip one"][0]
        
        
    def update_cameras(self):
        ## Change this, we don't need to undistort everytime i think
        ## We capture the frame and format it accordingly to be used by tkinter, 
        if debug == False:
            frame = cam_gear.get_cam_frame(self.stream1) 
            self.frame = self.cam.undistort(frame)
            self.invert = cv.invert(self.frame)  ### a quoi sert ce invert ??
            img = self.frame.copy()
            self.format_image(img, idx = 0)
        else:
            frame = cv2.imread("Pictures/cam2/failed_capture_0.png")
            self.format_image(frame, idx = 0)    
        self.macro_frame = cam_gear.get_cam_frame(self.stream2) 
        self.format_image(self.macro_frame, idx = 1)
        self.display_camera_feed()
        
        
    def format_image(self, img, idx):
        img = cv2.resize(img, (900, 500))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        self.frames[idx] = ImageTk.PhotoImage(image=img)
        # self.frames[idx] = ctk.CTkImage(img)
        
        
    def display_camera_feed(self):
        ## make this look nicer please
        self.camera_feed_mode.configure(image=self.frames[self.displayed_cameras-1])
        self.camera_feed_mode.image = self.frames[self.displayed_cameras-1]
        self.camera_feed_control.configure(image=self.frames[self.displayed_cameras-1])
        self.camera_feed_control.image = self.frames[self.displayed_cameras-1]
        
        self.camera_feed_camera_0.configure(image=self.frames[0])
        self.camera_feed_camera_0.image = self.frames[0]
        self.camera_feed_camera_1.configure(image=self.frames[1])
        self.camera_feed_camera_1.image = self.frames[1]
        
        
    #### Functions related to the parameter tab ####    
    def set_tab_parameters(self):
        self.param_tree_frame = ctk.CTkFrame(self.tabControl.tab("Parameters"))
        self.param_tree_frame.place(relx = 0.1, rely=0.2, relheight=0.8, relwidth=0.5)
        self.update_parameters()

        self.edit_parameter_frame = ctk.CTkFrame(self.tabControl.tab("Parameters"))
        self.edit_parameter_frame.place(relx = 0.6, rely=0.3)
        
        self.param_list = list(self.settings.keys())

        self.param_list.remove("Well")
        self.param_list.remove("Saved Positions")
        
        self.clicked_parameter_1 = ctk.StringVar()
        self.clicked_parameter_1.set(self.param_list[0])
        self.parameter_menu = ctk.CTkOptionMenu(self.edit_parameter_frame,
                                                variable=self.clicked_parameter_1,
                                                values = self.param_list,
                                                command=self.show_parameters)
        self.parameter_menu.grid(column=0, row=0, sticky="w")
        self.show_parameters(self.clicked_parameter_1.get())  ## maybe there's a way to not call this
        self.empty_label_param_1 = ctk.CTkLabel(self.edit_parameter_frame, text=" ").grid(column=0, row=1, sticky="w")


        # New Informative text at the top
        self.info_label = ctk.CTkLabel(self.tabControl.tab("Parameters"), 
                                    text="This is your informative text line at the top.",
                                    wraplength=500)  # Adjust wraplength as needed
        self.info_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)

        self.update_infotext()

        # Save as new filename button
        self.save_as_button = ctk.CTkButton(self.tabControl.tab("Parameters"), text="Save all settings as:", command=self.save_as)
        self.save_as_button.grid(row=1, column=0, padx=10, pady=10)

        # "Save as" text input box
        self.save_as_entry = ctk.CTkEntry(self.tabControl.tab("Parameters"), width=50)
        self.save_as_entry.grid(row=3, column=0, padx=10, pady=10)

        # Import from file button
        self.save_as_button = ctk.CTkButton(self.tabControl.tab("Parameters"), text="Import all settings from:", command=self.import_from)
        self.save_as_button.grid(row=2, column=0, padx=10, pady=10)

    def save_as(self):
        new_filename = self.save_as_entry.get()
        if print_all: print("Saving as new filename: ", new_filename)

        # If Saved Settings folder does not exist, create it
        if not os.path.exists("Saved Settings"):
            os.makedirs("Saved Settings")
        
        if not new_filename.endswith(".json"):
            new_filename += ".json"

        if new_filename in os.listdir("Saved Settings"):
            if print_all: print("File already exists. Overwriting.")
        else:
            if print_all: print("Creating new file.")
        
        new_filename = os.path.join("Saved Settings", new_filename)

        with open(new_filename, "w") as jsonFile:
            json.dump(self.settings, jsonFile, indent=4)
       
    def import_from(self):
        filename = self.save_as_entry.get()
        if print_all: print("Importing from filename: ", filename)
        
        if not filename.endswith(".json"):
            filename += ".json"

        # Does Saved Settings folder exist?
        if not os.path.exists("Saved Settings"):
            if print_all: print("'Saved Settings' folder does not exist.")
            if print_log: logger.error("'Saved Settings' folder does not exist.")
            return
        
        if filename in os.listdir("Saved Settings"):
            if print_all: print("File found. Importing.")
            with open(os.path.join("Saved Settings", filename), "r") as jsonFile:
                self.settings = json.load(jsonFile)
            self.update_parameters()
        else:
            if print_all: print("File not found. Please check the filename and try again.")
            if print_log: logger.error("File not found. Please check the filename and try again.")

    def update_infotext(self):
        # txt = "You have selected " + str(self.settings["Solution A"]["Solution A pumping volume"]) + " for the Solution A pumping volume, " + str(self.settings["Solution B"]["Solution B pumping volume"]) + " for the Solution B pumping volume and want to drop " + str(self.settings["Gel"]["Gel volume per well"]) + " into " + str(int(self.settings["Well"]["Number of well"])) + " well"
        # if self.settings["Well"]["Number of well"] > 1:
        #     txt += "s"
        txt = "You have selected " + str(self.settings["Solution A"]["Solution A pumping volume"]) + "ul for the Solution A pumping volume, " + str(self.settings["Solution B"]["Solution B pumping volume"]) + "ul for the Solution B pumping volume and want to drop " + str(self.settings["Gel"]["Gel volume per well"]) + "ul per well."
        txt += " You have selected " + str(int(self.settings["Well"]["Number of well"])) + " well"
        if self.settings["Well"]["Number of well"] > 1:
            txt += "s"
        txt += " and have " + str(int(self.settings["Gel"]["Number of mixing tubes"])) + " mixing tubes."
        clr = "black"
        # if self.settings["Solution A"]["Solution A pumping volume"] + self.settings["Solution B"]["Solution B pumping volume"] < self.settings["Gel"]["Gel volume per well"] * self.settings["Well"]["Number of well"]:
        if self.settings["Solution A"]["Solution A pumping volume"] + self.settings["Solution B"]["Solution B pumping volume"] < self.settings["Gel"]["Gel volume per well"]:
            clr = "red"
        if self.settings["Well"]["Number of well"] > (int(self.settings["Gel"]["Number of mixing tubes"])):
            clr = "red"
        if self.settings["Tissues"]["Number of samples per pick"] > 1:
            if print_log: logger.info(txt)
            txt = "With " + str(int(self.settings["Tissues"]["Number of samples per pick"])) + " sample"
            if self.settings["Tissues"]["Number of samples per pick"] > 1:
                txt += "s"
            txt += " per pick, the gel will not be used."
            clr = "black"
            if print_log: logger.info(txt)
        txt += " (" + str(int(self.settings["Tissues"]["Number of samples per pick"])) + " sample" 
        if self.settings["Tissues"]["Number of samples per pick"] > 1:
            txt += "s"
        txt += " per pick, " + str(int(self.settings["Tissues"]["Number of samples per well"])) + " sample"
        if self.settings["Tissues"]["Number of samples per well"] > 1:
            txt += "s"
        txt += " per well, in total: " + str(int(self.settings["Tissues"]["Number of samples per well"] * self.settings["Well"]["Number of well"])) + " sample"
        if self.settings["Tissues"]["Number of samples per well"] * self.settings["Well"]["Number of well"] > 1:
            txt += "s"
        txt += ")"
        self.info_label.configure(text=txt, text_color=clr)
        
    
    def show_parameters(self, click):
        try:
            self.sub_parameter_frame.grid_forget()
        except:
            pass
        self.sub_parameter_frame = ctk.CTkFrame(self.edit_parameter_frame, fg_color="transparent")
        self.sub_parameter_frame.grid(column=0, row=2, sticky="w")
        self.clicked_parameter_2 = ctk.StringVar()
        self.parameter_menu_2 = ctk.CTkOptionMenu(self.sub_parameter_frame,
                                                  variable=self.clicked_parameter_2,
                                                  values=list(self.settings[click].keys()))
        self.clicked_parameter_2.set(list(self.settings[click].keys())[0])
        self.parameter_menu_2.grid(column=0, row=0, sticky="w")
        
        self.empty_label_param_2 = ctk.CTkLabel(self.sub_parameter_frame, text=" ").grid(column=0, row=1, sticky="w")
        
        if type(list(self.settings[self.clicked_parameter_1.get()].values())[0]) == list: 
            self.entry_param_xyz = ctk.CTkFrame(self.sub_parameter_frame)
            self.entry_param_xyz.grid(column=0, row=2)
            self.entry_param_xyz_list = []
            self.entry_param_xyz_label = []
            for i in range(3):
                self.entry_param_xyz_label.append(ctk.CTkLabel(self.entry_param_xyz, text="X" if i==0 else "Y" if i==1 else "Z"))
                self.entry_param_xyz_label[i].grid(column=i, row=0, sticky="w", padx=5)
                self.entry_param_xyz_list.append(ctk.CTkEntry(self.entry_param_xyz, width=7))
                self.entry_param_xyz_list[i].grid(column=i, row=1, sticky="w", padx=5)
        else:
            self.entry_new_parameter = ctk.CTkEntry(self.sub_parameter_frame)
            self.entry_new_parameter.grid(column=0, row=3, sticky="w")
        
        self.empty_label_param_3 = ctk.CTkLabel(self.sub_parameter_frame, text=" ").grid(column=0, row=4, sticky="w")
        
        self.save_new_parameter_button = ctk.CTkButton(self.sub_parameter_frame, text="Save", command=self.save_new_parameter)
        self.save_new_parameter_button.grid(column=0, row=5, sticky="w")

    def save_new_parameter(self):
        
        param1 = self.clicked_parameter_1.get()
        param2 = self.clicked_parameter_2.get()
        if type(list(self.settings[param1].values())[0]) == list:
            temp_value = [None,None, None]
            for i in range(3):
                val = self.check_param_value(self.entry_param_xyz_list[i].get())
                if val == "Wrong value" :
                    return
                else:
                    temp_value[i] = val
            self.settings[param1][param2] = temp_value
        else:
            val = self.check_param_value(self.entry_new_parameter.get())
            if val == "Wrong value" :
                return
            else:
                self.settings[param1][param2] = val
        self.update_parameters()
        self.update_infotext()
   
   
    def check_param_value(self, val):
        val_return = True
        try:
            val_return = round(float(val), 2)
        except:
            if print_all: print("Incorrect input. Please write a number here. If your number uses a comma, please replace it with '.'")
            return "Wrong value"    
        return val_return
    
    
    def update_parameters(self):
        try:
            self.parameter_frame.place_forget()
        except:
            pass
        
        bg_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkFrame"]["fg_color"])
        text_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkLabel"]["text_color"])
        selected_color = self._apply_appearance_mode(ctk.ThemeManager.theme["CTkButton"]["fg_color"])
        treestyle = ttk.Style()
        treestyle.theme_use('default')
        treestyle.configure("Treeview", background=bg_color, foreground=text_color, fieldbackground=bg_color, borderwidth=0, font=('Arial', 12))
        treestyle.map('Treeview', background=[('selected', bg_color)], foreground=[('selected', selected_color)])
        self.bind("<<TreeviewSelect>>", lambda event: self.focus_set())
        
        self.parameter_treeview = ttk.Treeview(self.param_tree_frame, columns = ('Value',))
        self.parameter_treeview.heading('#0', text='Element')
        self.parameter_treeview.column("#0", width= 250)
        
        self.parameter_treeview.heading('Value', text='Value')
        self.parameter_treeview.column("Value", width= 100)
        
        self.populate_tree('', self.settings)
        self.parameter_treeview.place(relx=0.3, relheight=1)
              
           
    def populate_tree(self, parent, dictionary):
        sub_name = ['X', 'Y', 'Z']
        for key, value in dictionary.items():
            if type(value) == dict:
                item = self.parameter_treeview.insert(parent, 'end', text=key, open=False)
                self.populate_tree(item, value)
         
            elif type(value) == list:
                item1 = self.parameter_treeview.insert(parent, 'end', text=key, open=True)
                for i in range(3):
                    item = self.parameter_treeview.insert(item1, 'end', text=sub_name[i], values=[str(value[i])])	
            else:
                item = self.parameter_treeview.insert(parent, 'end', text=key, values=[str(value)])
    
        
    #### Functions related to the Well plate tab ####    
    def set_tab_well_plate(self):
        # call menu function
        # call well plate function
        
        self.clicked_well = tk.StringVar()

        self.well_menu = ctk.CTkOptionMenu(self.tabControl.tab("Well plate"),
                                           variable=self.clicked_well,
                                           values=self.options,
                                           command=self.show_wells)    
             
        self.well_menu.place(relx=0.3, rely=0.3, anchor=tk.CENTER)
        
        self.well_menu_description = ctk.CTkLabel(self.tabControl.tab("Well plate"), text="Select a well plate")
        self.well_menu_description.place(relx=0.3, rely=0.2, anchor=tk.CENTER)
        
        self.tab_well_explanation = ctk.CTkLabel(self.tabControl.tab("Well plate"),  
                                             text=self.text_well_plate_explanation,
                                             width=100,
                                             wraplength=500) 
        self.tab_well_explanation.place(relx=0.3, rely=0.4, anchor=tk.CENTER)
        
        self.text_well_results = ctk.StringVar() # shows a list of selected wells

        self.tab_well_results = ctk.CTkLabel(self.tabControl.tab("Well plate"),
                                             textvariable=self.text_well_results,
                                             width=100,
                                             wraplength=500) 
        self.tab_well_results.place(relx=0.3, rely=0.5, anchor=tk.CENTER)

        # self.text_well_results.set("You have selected the following wells:"+str(self.selected_wells)) # initial value for the selected wells
        
        self.text_remaining_wells = ctk.StringVar() # shows how many more wells you can still select
        self.remaining_wells = ctk.CTkLabel(self.tabControl.tab("Well plate"),
                                        textvariable=self.text_remaining_wells,
                                        width=100,
                                        wraplength=500)
        self.remaining_wells.place(relx=0.3, rely=0.55, anchor=tk.CENTER)

        # self.text_remaining_wells.set("You can still select "+str(6-len(self.selected_wells))+" wells") # initial value for the remaining wells
        
        
        self.well_button_grid = ctk.CTkFrame(self.tabControl.tab("Well plate"), width=300, height=480)
        
        self.well_button_grid.place(relx=0.3, rely=0.65, anchor=tk.CENTER)
        self.well_save_button = ctk.CTkButton(self.well_button_grid, 
                                           text="Save",
                                           command=self.save_well_settings)
        
        self.well_save_button.grid(column=0, row=0)
        self.well_reset_button = ctk.CTkButton(self.well_button_grid, 
                                            text="Reset", 
                                            command= lambda: self.show_wells(self.clicked_well.get())) 
        
        self.well_reset_button.grid(column=1, row=0)

        # initial type of well plate and initial selection of the first one!
        # self.clicked_well.set(self.options[2]) 
        self.clicked_well.set(self.settings["Well"]["Type"])
        self.show_wells(self.clicked_well.get())
        # self.toggle_well(3, self.layout[self.options.index(self.clicked_well.get())])
        for i in range(self.settings["Well"]["Number of well"]):
            self.toggle_well(self.label_row.index(self.settings["Well"][f"Culture {i+1}"][1]) + self.layout[self.options.index(self.clicked_well.get())][1] * (self.layout[self.options.index(self.clicked_well.get())][0] - 1 - self.label_col.index(self.settings["Well"][f"Culture {i+1}"][0])),
                              self.layout[self.options.index(self.clicked_well.get())])
        # self.settings["Well"]["Number of well"] = 1
        self.update_infotext()
        
            
    def show_wells(self, click):

        if print_all: print("show_wells called with click = ", click)
        
        ## rewrite this to include a try except for place_forget()
        self.selected_well_plate = click
        if self.well_plate_grid is not None: # check if it exists
            self.well_plate_grid.place_forget()
            self.selected_wells = []
            self.text_well_results.set("")
            self.text_remaining_wells.set("")
            for i in range(len(self.well_buttons)): 
                self.well_buttons[i].grid_forget()
            self.well_buttons = []
            
            
        self.set_well_plate(self.well_dim_x, self.well_dim_y, well_id = self.options.index(click))
         

    def set_well_plate(self, well_dim_x, well_dim_y, well_id):
        
        self.well_plate_grid = tk.Frame(self.tabControl.tab("Well plate"), width=300, height=480, bg="lightgray")
        self.well_plate_grid.place(relx=0.7, rely=0.5, anchor=tk.CENTER)
        index = 0
        for i in range(self.layout[well_id][0]):
            self.well_plate_grid.grid_columnconfigure(i, minsize=well_dim_x/self.layout[well_id][0])
            for j in range(self.layout[well_id][1]):
                self.well_plate_grid.grid_rowconfigure(j, minsize=well_dim_y/self.layout[well_id][1])
                self.well_buttons.append(tk.Button(self.well_plate_grid, 
                                                   text=self.label_col[self.layout[well_id][0] - 1 - i]+self.label_row[j], 
                                                   width=5, 
                                                   relief="raised", 
                                                   command=lambda idx = index: (self.toggle_well(idx, self.layout[well_id]))))
                self.well_buttons[index].grid(column=i, row=j) 
                index = index + 1
                
    
    def toggle_well(self, index, layout):
        button = self.well_buttons[index]
        temp = self.label_row[index%layout[1]]
        temp2 = self.label_col[layout[0] - 1 - index//layout[1]]
        if button['relief'] == "sunken":
            button.configure(relief = "raised")
            self.selected_wells.remove(temp2+temp)
            if len(self.selected_wells)==0:
                self.text_well_results.set("")
            
        else:
            if (len(self.selected_wells) < 6):
                button.configure(relief = "sunken")
                self.selected_wells.append(temp2+temp)
        if len(self.selected_wells)>0:
            self.text_well_results.set("You have selected the following wells:"+str(self.selected_wells))
            
        if len(self.selected_wells)==6:
            self.text_remaining_wells.set("You cannot select more wells") 
            self.remaining_wells.configure(text_color="red")
        else:
            self.text_remaining_wells.set("You can still select "+str(6-len(self.selected_wells))+" wells")
            self.remaining_wells.configure(text_color="black")
        
        
    def save_well_settings(self):
        self.settings["Well"]["Type"] = self.clicked_well.get()
        self.settings["Well"]["Number of well"] = len(self.selected_wells)
        for i in range(len(self.selected_wells)):
            self.settings["Well"][f"Culture {i+1}"] = self.selected_wells[i]    
        with open(SETTINGS, 'w') as f:
            json.dump(self.settings, f, indent=4)
        self.update_parameters()

        # Reset counts to zero
        self.well_num = 0
        self.well_nb_with_gel = 0
        self.nb_sample = 0

        self.update_infotext()


    #### Functions related to the motion control tab ####   
    def set_tab_motion_control(self):
        
        self.set_motor_control()
        self.set_servo_control()
        self.set_camera_for_control()

           
    def set_motor_control(self):
        
        gui_x_pos = 0.15
        gui_y_pos = .5
        self.xyz_gui_position = ctk.CTkFrame(self.tabControl.tab("Motion Control"))
        self.xyz_gui_position.place(relx=gui_x_pos, rely=gui_y_pos, anchor=tk.CENTER)
        steps = [0.1, 1, 5, 10, 25, 50]
        coords_name = ["X", "Y", "Z"]
        
        self.set_toolhead_menus(gui_x_pos)
        
        self.button_right = ArrowButtonRight(self.xyz_gui_position, target_class=self, printer_class=self.anycubic)
        self.button_right.grid(column=2, row=2, padx=10, pady=10)
        
        self.button_left = ArrowButtonLeft(self.xyz_gui_position, target_class=self, printer_class=self.anycubic)
        self.button_left.grid(column=0, row=2, padx=10, pady=10)
        
        self.button_top = ArrowButtonTop(self.xyz_gui_position, target_class=self, printer_class=self.anycubic)
        self.button_top.grid(column=1, row=1, padx=10, pady=10)
        
        self.button_bottom = ArrowButtonBottom(self.xyz_gui_position, target_class = self, printer_class=self.anycubic)
        self.button_bottom.grid(column=1, row=3, padx=10, pady=10)
        
        self.center_button = RoundButton(self.xyz_gui_position, diameter=50, bg_color="black", target_class=self, printer_class=self.anycubic)
        self.center_button.grid(column=1, row=2, padx=10, pady=10)
        self.z_button_up = ArrowButtonTop(self.xyz_gui_position, is_z=True, target_class = self, printer_class=self.anycubic)
        self.z_button_up.grid(column=3, row=1, padx=10, pady=10)
        
        self.z_button_down = ArrowButtonBottom(self.xyz_gui_position, is_z=True, target_class = self, printer_class=self.anycubic)
        self.z_button_down.grid(column=3, row=3, padx=10, pady=10)
        
        
        self.z_label = ctk.CTkLabel(self.xyz_gui_position, text=coords_name[2])
        self.z_label.grid(column=3, row=2, padx=10, pady=10)                      
        
        #### maybe move this into the self.xyz_gui_position frame
        self.xyz_step_buttons_text = ctk.CTkLabel(self.tabControl.tab("Motion Control"), text="Step value")
        self.xyz_step_buttons_text.place(relx=gui_x_pos+0.015, rely=gui_y_pos-.3, anchor=tk.CENTER)
        
        self.xyz_step_buttons = ctk.CTkSegmentedButton(self.tabControl.tab("Motion Control"),
                                                       values=steps)
        self.xyz_step_buttons.place(relx=gui_x_pos+0.015, rely=gui_y_pos-.23, anchor=tk.CENTER, relwidth=0.22)
        self.xyz_step_buttons.set(steps[0])
        
        
        self.coord_value_grid = ctk.CTkFrame(self.tabControl.tab("Motion Control"))
        self.coord_value_grid.place(relx=gui_x_pos+0.015, rely= gui_y_pos+0.35, anchor=tk.CENTER)
        
        for i in range(len(coords_name)):
            self.coord_label.append(ctk.CTkLabel(self.coord_value_grid, text=coords_name[i])) 
            self.coord_label[i].grid(column=i, row=5, padx=17, pady=10)
            
            self.coord_value_text.append(ctk.StringVar())
            self.coord_value.append(ctk.CTkEntry(self.coord_value_grid,
                                                 width=7,
                                                 textvariable=self.coord_value_text[i],
                                                 state='readonly'))  
            self.coord_value[i].grid(column=i, row=6, pady=10, ipadx=15)
        
        self.move_xyz_button = ctk.CTkButton(self.coord_value_grid, text="Move", command=lambda: self.move_xyz(move_button_cmd=True))
        self.move_xyz_button.grid(column=0, row=7, pady=15, sticky="e") 
        
        self.reset_axis_button = ctk.CTkButton(self.coord_value_grid, text="Reset axis", command=self.reset_axis)
        self.reset_axis_button.grid(column=2, row=7, pady=15, sticky="w")
    
    
    def set_toolhead_menus(self, gui_x_pos):
       
        self.pipette_selector_frame = ctk.CTkFrame(self.tabControl.tab("Motion Control"))
        self.pipette_selector_frame.place(relx=gui_x_pos+0.015, rely=0.07, anchor=tk.CENTER)
        self.pipette_name = list(self.settings.get("Offset").keys())
        self.pipette_name.remove("Fixed Camera")
        self.pipette_name.remove("Fixed Camera 2")
        
        self.offset_selector_text = ctk.CTkLabel(self.pipette_selector_frame, text="Toolhead's offset")
        self.offset_selector_text.grid(column=0, row=0, padx=10, pady=5)
        
        self.clicked_offset = ctk.StringVar()
        self.pipette_offset_selector = ctk.CTkOptionMenu(self.pipette_selector_frame,
                                                         variable=self.clicked_offset,
                                                         values=self.pipette_name,
                                                         command=self.select_offset)
        self.clicked_offset.set(self.pipette_name[0])
        self.pipette_offset_selector.grid(column=0, row=1)

        self.pipette_selector_text = ctk.CTkLabel(self.pipette_selector_frame, text="Toolhead's servo's position")
        self.pipette_selector_text.grid(column=1, row=0, padx=10, pady=5)
        
        self.clicked_pipette = ctk.StringVar()
        self.pipette_selector = ctk.CTkOptionMenu(self.pipette_selector_frame,
                                                  variable=self.clicked_pipette,
                                                  values=self.toolhead_position,
                                                  command=self.select_tip)
        
        self.clicked_pipette.set(self.toolhead_position[0])
        
        self.pipette_selector.grid(column=1, row = 1) 

        # Initial state of the selectors
        self.clicked_pipette.set(self.toolhead_position[self.tip_number])
        
    
    def select_tip(self, value):

        if self.is_homed == False:
            if print_all: print("You need to home the printer first")
            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            self.clicked_pipette.set(self.toolhead_position[self.tip_number])
            return

        # make it so it also changes the offset maybe, both internally and visually(GUI)
        self.move_xyz(go_safe_height=True) 

        self.tip_number = self.toolhead_position.index(value)
        if print_all: print("Selected tip number is {}".format(value))
        if print_all: print(" This corresponds to number ", self.toolhead_position.index(value))

        self.dynamixel.select_tip(tip_number=self.toolhead_position.index(value), ID=3)     
        
        
    def select_offset(self, value):

        if self.is_homed == False:
            if print_all: print("You need to home the printer first")
            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            return
        
        self.offset = self.settings["Offset"][value]  
        ### ajouter un wait peut etre pour pas qu'il le fasse en même temps
        self.move_xyz(go_safe_height=True) 
      
    def set_speed(self, x, y, z):
        self.anycubic.max_x_feedrate(x)
        self.anycubic.max_y_feedrate(y)
        self.anycubic.max_z_feedrate(z)

    def move_home(self):
        
        self.anycubic.homing()
        # self.anycubic.max_x_feedrate(300)
        # self.anycubic.max_y_feedrate(300)
        # self.anycubic.max_z_feedrate(25) 

        self.set_speed(300, 300, 25)

        self.anycubic.move_home()
        
        self.is_homed = True    
        [self.coord_value_text[i].set(0) for i in range(3)]
        [self.coord_value[i].configure(state='normal') for i in range(3)]

        if print_all: print("Homing complete")
        
        
    def move_xyz(self, x=0, y=0, z=0, move_button_cmd=False, go_safe_height = False):
        # REWRITE THIS FUNCTION TO HAVE ONE PER AXIS, SO ITS EASIER TO HANDLE AXIS SPECIFIC COMMANDS
        ## maybe add a drop down menu with a list of every known position as to make everything faster
        ## maybe add a drop down menu setting the speeds !
        
        offset = self.offset.copy()
        for i in range(len(self.coord_value_text)):
            if move_button_cmd:
                try:
                    float(self.coord_value_text[i].get())
                except:
                    if print_all: print("You need to enter XYZ coords as value, with '.', not letters or other symbols")
                    return
        if move_button_cmd or go_safe_height:
            x = round(float(self.coord_value_text[0].get()),2)
            y = round(float(self.coord_value_text[1].get()),2)
            z = round(float(self.coord_value_text[2].get()),2)
        else:
            x = round(float(self.coord_value_text[0].get()) + x,2)
            y = round(float(self.coord_value_text[1].get()) + y,2)
            z = round(float(self.coord_value_text[2].get()) + z,2)
            
        if go_safe_height:
            z = self.safe_height
            
        if x < X_MIN-offset[0]:
            x = X_MIN-offset[0]
        elif x > X_MAX:
            x = X_MAX
        if y < Y_MIN:
            y = Y_MIN
        elif y > Y_MAX:
            y = Y_MAX
        if z < Z_MIN:
            z = Z_MIN
        elif z > Z_MAX:
            z = Z_MAX
            
        if print_all: print("Setting position to X={}, Y={}, Z={}".format(x,y,z))
        if print_all: print("Offset is {}".format(self.offset))
        
        
        if (x < -offset[0]) or (self.last_pos[0] < -offset[0]):
            delta = round(x - self.last_pos[0],2)
            # if print_all: print(delta)
            if delta < 0: # we go further into the negative
                self.anycubic.set_position(x = -delta) 
            elif x < 0: # we go in positive direction, but still in negative
                self.anycubic.set_position(x = -delta) # this WORKS
            else: # we return to positive domain
                self.anycubic.set_position(x = self.last_pos[0])
            
        if print_all: print("offset is {}".format(offset))
        if print_all: print("x is {}".format(x))
        self.anycubic.move_axis_relative(x=x, y=y, z=z, offset=offset)
        self.coord_value_text[0].set(str(x))
        self.coord_value_text[1].set(str(y))
        self.coord_value_text[2].set(str(z))
        self.last_pos = [x,y,z]
        # Maybe find a way to read the coordinate instead of writing them manually into self.coord_value_text  
        
    
    def reset_axis(self):
        if not debug:
            self.anycubic.disable_axis(all=True)
        self.offset = [0,0,0]
        self.clicked_offset.set(self.pipette_name[0])
        for i in range(3):
            self.coord_value_text[i].set("")
            self.coord_value[i].configure(state='readonly')
        self.is_homed = False
        
                
    def set_servo_control(self):

        gui_x_pos = 0.85
        gui_y_pos = 0.5
        spacing = 20
        steps = [1, 5, 10, 25, 50, 100]
        
        button_height = 7
        
        self.servo_gui_position = ctk.CTkFrame(self.tabControl.tab("Motion Control"), fg_color="transparent")
        self.servo_gui_position.place(relx=gui_x_pos+.015, rely=gui_y_pos, anchor=tk.CENTER)
        
        self.clicked_servo_unit = ctk.StringVar()
        self.clicked_servo_unit.set(self.unit_list[0])
        self.servo_unit_list_menu = ctk.CTkOptionMenu(self.tabControl.tab("Motion Control"),
                                                      variable=self.clicked_servo_unit,
                                                      values=self.unit_list,
                                                      command=self.display_servo_pos)
        self.servo_unit_list_menu.place(relx=gui_x_pos, rely=0.10, anchor=tk.CENTER)
        
        #### Buttons for deciding the values of the steps
        
        self.servo_step_buttons_text = ctk.CTkLabel(self.tabControl.tab("Motion Control"), text="Step value")
        self.servo_step_buttons_text.place(relx=gui_x_pos, rely=gui_y_pos-.3, anchor=tk.CENTER)
        
        self.servo_step_buttons = ctk.CTkSegmentedButton(self.tabControl.tab("Motion Control"),
                                                         values=steps)
        self.servo_step_buttons.place(relx=gui_x_pos, rely=gui_y_pos-.23, anchor=tk.CENTER, relwidth=0.22)
        self.servo_step_buttons.set(steps[0])
        
        self.set_servo_buttons(button_height, spacing)
        
        #### Buttons for saving the positions of the servos and the motors
        self.save_position_gui = ctk.CTkFrame(self.tabControl.tab("Motion Control"))
        self.save_position_gui.place(relx=gui_x_pos, rely=gui_y_pos+0.3, anchor=tk.CENTER)   
        
        
        self.purge_button_text = ctk.StringVar()
        self.purge_button_text.set("Purging OFF")
        self.purge_button = ctk.CTkButton(self.save_position_gui, 
                                       textvariable=self.purge_button_text, 
                                       command=self.purge)
        self.purge_button.grid(column=0, row=0, pady=20)
        
        self.save_text = ctk.CTkLabel(self.save_position_gui, text=f'''You can save the current positions of the motor and the servo.  \n They will be saved in the {SETTINGS} as : ''')
        self.save_text.grid(column=0, row=1)
        
        self.save_position_gui.rowconfigure(2, minsize=20, weight=1)
        
        self.save_name_entry = ctk.CTkEntry(self.save_position_gui, width=100)
        self.save_name_entry.grid(column=0, row=3, padx=5)
        
        self.save_position_gui.rowconfigure(4, minsize=10, weight=1)
        
        self.save_pos_button = ctk.CTkButton(self.save_position_gui, text="Save", command=self.save_pos)
        self.save_pos_button.grid(column=0, row=5)
     
     
    def set_servo_buttons(self, button_height, spacing):
        text = ["Eject", "Pump"]
        
        for i in range(len(self.servo_names)):
            if i == 2:
                text = ["+", "-"]
            self.servo_frame.append(ctk.CTkFrame(self.servo_gui_position))
            self.servo_frame[i].grid(column=i, row=0, ipadx=spacing)
            
            self.servo_labels.append(ctk.CTkLabel(self.servo_frame[i], text=self.servo_names[i]))
            self.servo_labels[i].grid(column=0, row=0, pady = 10)
            self.servo_buttons.append(ctk.CTkButton(self.servo_frame[i], 
                                                 text=text[0], 
                                                 width=50,
                                                 command = lambda idx = i: self.move_servo('+', idx)))
            self.servo_buttons[2*i].grid(column=0, row=1, ipady=button_height)
            
            self.servo_buttons.append(ctk.CTkButton(self.servo_frame[i], 
                                                 text=text[1], 
                                                 width=50,
                                                 command = lambda idx = i: self.move_servo('-', idx)))
            self.servo_buttons[2*i+1].grid(column=0, row=2, ipady=button_height)
            
            self.servo_values_text.append(ctk.StringVar())
            self.servo_values_text[i].set(self.servo_pos[i])
            self.servo_values.append(ctk.CTkLabel(self.servo_frame[i], textvariable=self.servo_values_text[i]))
            self.servo_values[i].grid(column=0, row=5, pady = 15)
            
            
    def purge(self):
        ### MAKE SURE THIS HAPPENS ONLY AT 0: OR SOME SORT OF SECURITY
         if self.purge_button_text.get() == "Purging OFF":
             self.purge_button_text.set("Purging ON")
             self.purging = True
         else:
            self.purge_button_text.set("Purging OFF")
            self.purging = False
         
         
    def move_servo(self, sign, idx):
        
        ## add something for the purge here
        if not(self.clicked_servo_unit.get() == self.unit_list[1]) or idx == 2:
            delta = self.servo_step_buttons.get()*(1 if sign == '+' else -1)
        else:
            delta = self.servo_step_buttons.get()*(1 if sign == '+' else -1)*self.pipette_empty/100
            
        self.servo_pos[idx] = round(self.servo_pos[idx] + delta,1)
            
        if idx == 2:
            if self.servo_pos[idx] > 100:
                self.servo_pos[idx] = 100
            elif self.servo_pos[idx] < 0:
                self.servo_pos[idx] = 0
            self.dynamixel.write_profile_velocity(self.servo_pos[idx], ID=[1,2])
            self.servo_values_text[idx].set(self.servo_pos[idx])
        else:
            if self.servo_pos[idx] > self.pipette_empty and self.purging == False:
                self.servo_pos[idx] = self.pipette_empty
            elif self.servo_pos[idx] > self.pipette_max_ul and self.purging == True:
                self.servo_pos[idx] = self.pipette_max_ul
            elif self.servo_pos[idx] < 0:
                self.servo_pos[idx] = 0

            self.dynamixel.write_pipette_ul(volume_ul=self.servo_pos[idx], ID=idx+1, purging = self.purging)
            self.display_servo_pos()
        
        if print_pipette_state:
            # print("Pipette 1 position: ", self.pipette_1_pos, "Pipette 2 position: ", self.pipette_2_pos)
            print("Servo 1 position: ", self.servo_pos[0], "Servo 2 position: ", self.servo_pos[1])
        
        
    def set_camera_for_control(self):
        self.camera_control_frame = ctk.CTkFrame(self.tabControl.tab("Motion Control"))
        self.camera_control_frame.place(relx=0.5, rely=0.35, anchor=tk.CENTER)  
           
        self.control_camera_button = ctk.CTkButton(self.camera_control_frame, 
                                                textvariable=self.camera_displayed_text, 
                                                command=self.show_camera_control)
        self.control_camera_button.pack()
        
        self.camera_feed_control = ctk.CTkLabel(self.camera_control_frame, text="", width=480, height=270)
        self.camera_feed_control.pack()
    
    
    def show_camera_control(self): 
        if self.camera_displayed_text.get() == "Camera 1":
            self.camera_displayed_text.set("Camera 2")
            self.displayed_cameras = 2
        else:
            self.camera_displayed_text.set("Camera 1")
            self.displayed_cameras = 1
            
    
    def display_servo_pos(self, event=None):
        
        if self.clicked_servo_unit.get() == self.unit_list[1]:
            self.servo_values_text[0].set(str(round(self.servo_pos[0]/self.pipette_empty*100,1))+"%")
            self.servo_values_text[1].set(str(round(self.servo_pos[1]/self.pipette_empty*100,1))+"%")   
        elif self.clicked_servo_unit.get() == self.unit_list[2]:
            self.servo_values_text[0].set(str(round(self.pipette_empty-self.servo_pos[0],1))+"μl")
            self.servo_values_text[1].set(str(round(self.pipette_empty-self.servo_pos[1],1))+"μl")   
        else:
            self.servo_values_text[0].set(str(self.servo_pos[0]))
            self.servo_values_text[1].set(str(self.servo_pos[1]))
            
    
    def save_pos(self):
        if self.settings.get('Saved Positions') == None:
            self.settings['Saved Positions'] = {}
        var = self.save_name_entry.get()
        self.settings['Saved Positions'][var] = {}
        self.settings['Saved Positions'][var]["X"] = self.coord_value_text[0].get()
        self.settings['Saved Positions'][var]["Y"] = self.coord_value_text[1].get()
        self.settings['Saved Positions'][var]["Z"] = self.coord_value_text[2].get()
        self.settings['Saved Positions'][var]["Servo 1"] = self.servo_pos[0]
        self.settings['Saved Positions'][var]["Servo 2"] = self.servo_pos[1]
        self.settings['Saved Positions'][var]["Servo Speed"] = self.servo_pos[2] 
        self.update_parameters()

            
    def add_function_to_buffer(self, function, *args):
        # add a function to the buffer
        # function is the function to be executed
        # *args are the arguments of the function
        self.buffer_moves.append([function, args])
        
        
    def execute_function_from_buffer(self):
        # check if current move is done
        # if yes, removes first entry from buffer and executes it
        # if no, return
        # if move is done:
        #     self.buffer_moves.pop(0)
        #     self.buffer_moves[0][0](*self.buffer_moves[0][1]) ## maybe remove star
        pass
        
        
    def set_tab_documentation(self):

       # Clear existing widgets in the tab
        for widget in self.tabControl.tab("Documentation").winfo_children():
            widget.destroy()

        # Get the frame for the "Documentation" tab
        documentation_frame = self.tabControl.tab("Documentation")

        # Load and display the image
        try:
            image_path = "Manual.png"  # Replace with your actual image file
            img = Image.open(image_path)

            original_img = Image.open(image_path)

            ##################
            # Get the width of the documentation frame
            frame_width = 2144

            # Calculate new height to maintain aspect ratio
            aspect_ratio = original_img.width / original_img.height
            new_height = int(frame_width / aspect_ratio)

            # Resize the image
            # print("Resizing image to", frame_width, "x", new_height, "instead of", original_img.width, "x", original_img.height)
            img = original_img.resize((frame_width, new_height), Image.Resampling.LANCZOS)
            #######################

            # Resize if needed (optional)
            # img = img.resize((1200, 900), Image.Resampling.LANCZOS)  # Adjust size as needed

            photo = ImageTk.PhotoImage(img)

            # Canvas to make the image scrollable
            canvas = tk.Canvas(documentation_frame)
            canvas.pack(side=tk.LEFT, fill="both", expand=True)

            # Scrollbar for the canvas
            scrollbar = ttk.Scrollbar(documentation_frame, orient=tk.VERTICAL, command=canvas.yview)
            scrollbar.pack(side=tk.RIGHT, fill="y")
            canvas.configure(yscrollcommand=scrollbar.set)


            # Display the image on the canvas
            canvas.create_image(0, 0, anchor="nw", image=photo)
            canvas.image = photo  # Keep a reference to prevent garbage collection

            # Configure the canvas to be scrollable
            canvas.configure(scrollregion=canvas.bbox("all"))

            # Bind mousewheel event for scrolling (if needed)
            def _on_mousewheel(event):
                # Only scroll if the "Documentation" tab is active
                if print_all: print(" We are in tab: ", self.tabControl.get())
                if self.tabControl.get() == self.tabs_name[5]:
                    canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            canvas.focus_set()  # Set focus to the canvas


        except FileNotFoundError:
            tk.Label(documentation_frame, text=f"Error: File '{image_path}' not found.").pack()


     
               
    def close_window(self):  
        # with open(SETTINGS, "w") as jsonFile:
        #     json.dump(self.settings, jsonFile, indent=4)
        # try :
        #     self.stream2.stop()
        # except:
        #     pass
        # try:
        #     self.stream1.stop()
        # except:
        #     pass
        # self.isOpen = False
     


        # Reworked version:
        # print("Closing the window")

        # Save the current settings to a file
        try:
            with open(SETTINGS, "w") as jsonFile:
                json.dump(self.settings, jsonFile, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

        # Stop camera streams 
        try:
            if hasattr(self, 'stream2') and self.stream2 is not None:
                self.stream2.stop()
                self.stream2.join()
        except Exception as e:
            print(f"Error stopping stream2: {e}")

        try:
            if hasattr(self, 'stream1') and self.stream1 is not None:
                self.stream1.stop()
                self.stream1.join()
        except Exception as e:
            print(f"Error stopping stream1: {e}")

        # Stop stopwatch
        self.stop_stopwatch()
        self.running = False

        # Cancel `after` callbacks
        try:
            if hasattr(self, '_after_id'):
                self.after_cancel(self._after_id)
        except Exception as e:
            print(f"Error cancelling after callback: {e}")


        # Mark the window as closed
        self.isOpen = False

        # Destroy the main window to close the application
        try:
            self.destroy()
        except Exception as e:
            print(f"Error destroying window: {e}")

        # print("Window closed")


#################################################################################################################################
#                                                     Calibration functions                                                     #
#################################################################################################################################

        
    def calibration_process(self, key, offset):
        
        # if print_all: print("Key pressed is {}".format(key))
        # if print_all: print(key)

        incr = 0.1
                
        # if key == 2424832: #Right
        if key == "Right": #Right
            offset[0] += incr
            if print_all: print("Left right offset is: ", offset[0])
            self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)
            
        # elif key == 2555904: #Left
        elif key == "Left": #Left
            offset[0] -= incr
            if print_all: print("Left right offset is: ", offset[0])
            self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        # if key == 2490368: #Up
        if key == "Up": #Forward
            offset[1] += incr
            self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        #elif key == 2621440:#Down
        elif key == "Down": #Backward
            offset[1] -= incr
            self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        # elif key == ord('u'):
        elif key == "u" or key == "U": #Up
            offset[2] += incr
            self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        #elif key == ord('d'):
        elif key == "d" or key == "D": #Down
            offset[2] -= incr
            self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        return offset
    
    def calibration_process_camera(self, key, offset):
        
        # if print_all: print("Key pressed is {}".format(key))
        # if print_all: print(key)

        incr = 0.1
                
        # if key == 2424832: #Right
        if key == "Right": #Right
            offset[0] += incr
            if print_all: print("Left right offset is: ", offset[0])
            self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)
            
        # elif key == 2555904: #Left
        elif key == "Left": #Left
            offset[0] -= incr
            if print_all: print("Left right offset is: ", offset[0])
            self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        # if key == 2490368: #Up
        if key == "Up": #Forward
            offset[1] += incr
            self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        #elif key == 2621440:#Down
        elif key == "Down": #Backward
            offset[1] -= incr
            self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        # elif key == ord('u'):
        elif key == "u" or key == "U": #Up
            offset[2] += incr
            self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        #elif key == ord('d'):
        elif key == "d" or key == "D": #Down
            offset[2] -= incr
            self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)

        return offset


    def fullcalibration(self):
        # Update the message box to indicate calibration start
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Full Calibration started")
        self.message_box.see(tk.END)
        self.update_idletasks()  # Force GUI update

        self.move_home()
        

        if hasattr(self, 'camera_feed_frame') and self.camera_feed_frame.winfo_exists():
            self.camera_feed_frame.destroy()
            
        self.camera_feed_frame = tk.Frame(self.tabControl.tab("Mode"))
        # Adjust the row and padding to lower the frame
        self.camera_feed_frame.grid(row=1, column=1, padx=10, pady=20, rowspan=10)

        # Create a label to show the camera feed within the frame
        self.camera_feed_label = tk.Label(self.camera_feed_frame)
        self.camera_feed_label.grid(row=0, column=0)

        # Bind key events
        self.bind('<Key>', self.on_key_press)

        # Macro camera calibration
        if not debug:
            self.anycubic.set_position(x=-self.x_firmware_limit_overwrite)
        self.anycubic.move_axis_relative(x=self.picture_pos, offset=self.settings["Offset"]["Tip one"])

        # self.dynamixel.select_tip(tip_number=2, ID=3)
        self.dynamixel.select_tip(tip_number=1, ID=3)
        # Depending on what tip will come to the fixed camera

        # self.anycubic.move_axis_relative(x=self.settings["Offset"]["Fixed Camera"][0], y=self.settings["Offset"]["Fixed Camera"][1], z=self.settings["Offset"]["Fixed Camera"][2], offset=[0,0,0])
        # self.anycubic.move_axis_relative(x=self.settings["Offset"]["Fixed Camera"][0], y=self.settings["Offset"]["Fixed Camera"][1])
        self.anycubic.move_axis_relative(x=0, y=self.settings["Offset"]["Calibration point"][1],z=self.settings["Offset"]["Calibration point"][2], offset=self.settings["Offset"]["Fixed Camera"])

        # self.move_xyz(x=self.settings["Offset"]["Fixed Camera"][0], y=self.settings["Offset"]["Fixed Camera"][1], z=self.settings["Offset"]["Fixed Camera"][2])
                            
        self.camera_displayed_text.set("Camera 2")
        self.displayed_cameras = 2

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Calibrate with arrows, U and D, and press Enter to continue")
        self.message_box.see(tk.END)
        self.update_idletasks() 

        self.key_pressed = "Down"
        while True:
            self.macro_frame = cam_gear.get_cam_frame(self.stream2)
            self.show_frame(self.macro_frame)  # Show the frame in the main window

            if self.key_pressed == 'Return':  # Enter key
                self.key_pressed = None
                break

            elif self.key_pressed is not None:
                self.settings["Offset"]["Fixed Camera"] = self.calibration_process_camera(self.key_pressed, self.settings["Offset"]["Fixed Camera"])
                self.key_pressed = None

            self.update_idletasks()
            self.update()

        self.reference = self.macro_frame.copy()
        # Save it as the reference picture in the macro folder
        macro_dir = r"Pictures/macro"
        if not os.path.exists(macro_dir):
            os.makedirs(macro_dir)
        
        cv2.imwrite("Pictures/macro/reference.png", self.reference)


        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Fixed Camera Calibrated")
        self.message_box.see(tk.END)
        self.update_idletasks() 

        # Same for the second pipette
        self.dynamixel.select_tip(tip_number=2, ID=3)

       
        self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], 
                                            offset=self.settings["Offset"]["Fixed Camera 2"])

        self.key_pressed = None
        while True:
            self.macro_frame = cam_gear.get_cam_frame(self.stream2)
            self.show_frame(self.macro_frame)  # Show the frame in the main window

            if self.key_pressed == 'Return':  # Enter key
                self.key_pressed = None
                break

            elif self.key_pressed is not None:
                self.settings["Offset"]["Fixed Camera 2"] = self.calibration_process_camera(self.key_pressed, self.settings["Offset"]["Fixed Camera 2"])
                self.key_pressed = None

            

            self.update_idletasks()
            self.update()

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Fixed Camera Calibrated with pipette 2")
        self.message_box.see(tk.END)
        self.update_idletasks() 


        self.anycubic.move_axis_relative(z=self.safe_height, offset=self.settings["Offset"]["Tip one"])
        self.anycubic.move_axis_relative(x=-self.x_firmware_limit_overwrite)
        if not debug:
            self.anycubic.set_position(x=0)

        self.tip_calibration() 

    def tip_calibration(self): # Common part to full and offset calibrations
        
        # tips and micro camera calibration
        self.dynamixel.select_tip(tip_number=1, ID=3)  
        
        # Offset first tip calibration
        #self.anycubic.move_axis_relative(z=5, offset=self.settings["Offset"]["Tip one"])
        #self.anycubic.move_axis_relative(x=5, y=-15, offset=self.settings["Offset"]["Tip one"])
        self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], y=self.settings["Offset"]["Calibration point"][1], z=10, offset=self.settings["Offset"]["Tip one"])
        
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            if debug:
                imshow = cam_gear.get_cam_frame(self.stream2)
            else:
                frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)
                imshow = self.frame.copy()

            self.show_frame(imshow)  # Show the frame in the main window

            self.update_idletasks()
            self.update()

        self.anycubic.move_axis_relative(z=self.settings["Offset"]["Calibration point"][2], offset=self.settings["Offset"]["Tip one"])

        #self.show_camera_control()

        while True:
            if debug:
                imshow = cam_gear.get_cam_frame(self.stream2)
            else:
                frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)
                self.invert = cv.invert(self.frame)
                imshow = self.frame.copy()
            
            self.show_frame(imshow)  # Show the frame in the main window
            
            if self.key_pressed == 'Return':  # Enter key
                if print_all: print("Offset tip one: ", self.settings["Offset"]["Tip one"])
                self.key_pressed = None
                break

            elif self.key_pressed is not None:
                self.settings["Offset"]["Tip one"] = self.calibration_process(self.key_pressed, self.settings["Offset"]["Tip one"])
                self.key_pressed = None

            

            self.update_idletasks()
            self.update()
        
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Tip 1 Calibrated")
        self.message_box.see(tk.END)
        self.update_idletasks() 

        self.anycubic.move_axis_relative(z=self.safe_height, offset=self.settings["Offset"]["Tip one"])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            
            if debug:
                imshow = cam_gear.get_cam_frame(self.stream2)
            else:
                frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)
                imshow = self.frame.copy()

            self.show_frame(imshow)  # Show the frame in the main window
            self.update_idletasks()
            self.update()

        self.tip_number = 2
        self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
        
        self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], y=self.settings["Offset"]["Calibration point"][1], offset=self.settings["Offset"]["Tip two"])
        self.anycubic.move_axis_relative(z=self.settings["Offset"]["Calibration point"][2], offset=self.settings["Offset"]["Tip two"])

        while True:
            if debug:
                imshow = cam_gear.get_cam_frame(self.stream2)
            else:
                frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)
                self.invert = cv.invert(self.frame)
                imshow = self.frame.copy()
            
            self.show_frame(imshow)  # Show the frame in the main window
            
            if self.key_pressed == 'Return':  # Enter key
                if print_all: print("Offset tip two: ", self.settings["Offset"]["Tip two"])
                self.key_pressed = None
                break

            elif self.key_pressed is not None:
                self.settings["Offset"]["Tip two"] = self.calibration_process(self.key_pressed, self.settings["Offset"]["Tip two"])
                self.key_pressed = None

            

            self.update_idletasks()
            self.update()

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Tip 2 Calibrated")
        self.message_box.see(tk.END)
        self.update_idletasks() 
        
        # self.anycubic.move_axis_relative(z=self.safe_height, offset=self.settings["Offset"]["Tip one"])
        self.anycubic.move_axis_relative(z=self.safe_height, offset=self.settings["Offset"]["Camera"])
        # Why would this be Offset Tip 1 ???

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            if debug:
                imshow = cam_gear.get_cam_frame(self.stream2)
            else:
                frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)
                imshow = self.frame.copy()

            self.show_frame(imshow)  # Show the frame in the main window

            self.update_idletasks()
            self.update()
            
        self.tip_number = 1
        self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
            
        self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=self.settings["Offset"]["Camera"])
        

        while True:
            if debug:
                imshow = cam_gear.get_cam_frame(self.stream2)
            else:
                frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)
                #self.invert = cv.invert(self.frame)

                # Rotate the image 90 degrees to the left
                imshow = cv2.rotate(self.frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

                imshow = self.frame.copy()
            
            # Draw a cross in the center of the image to calibate the camera on the hole
            markerSize = 15
            thickness = 1
            center = (imshow.shape[1] // 2, imshow.shape[0] // 2)
            # imshow = cv2.drawMarker(imshow, center, (255, 0, 0), cv2.MARKER_CROSS, markerSize, thickness)
            imshow = cv2.drawMarker(imshow, center, (0, 255, 0), cv2.MARKER_CROSS, markerSize, thickness)

            self.show_frame(imshow)  # Show the frame in the main window
            

            if self.key_pressed == 'Return':  # Enter key
                if print_all: print("Offset cam: ", self.settings["Offset"]["Camera"])
                self.key_pressed = None
                break
            
            elif self.key_pressed is not None:
                self.settings["Offset"]["Camera"] = self.calibration_process(self.key_pressed, self.settings["Offset"]["Camera"])
                self.key_pressed = None

            self.update_idletasks()
            self.update()
            

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Camera Calibrated")
        self.message_box.see(tk.END)
        self.update_idletasks() 

     
        # The calibration of the pixel position of the tip needs to be rethought
        ###########################################################################################     
        # if not debug:
        #     self.tip_pos_px = self.cam.platform_space_to_cam(self.settings["Offset"]["Tip one"], self.settings["Offset"]["Camera"])
        #     # small corrections: (May god know why....)
        #     self.tip_pos_px[0] += 561
        #     self.tip_pos_px[1] -= 311

        #     if print_all: print("Tip position in pixels: ", self.tip_pos_px)
        ############################################################################################

        # Manual calibration of the tip position in pixels
        while True:
            if debug:
                imshow = cam_gear.get_cam_frame(self.stream2)
            else:
                frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)
                #self.invert = cv.invert(self.frame)

                # Rotate the image 90 degrees to the left
                imshow = cv2.rotate(self.frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

                imshow = self.frame.copy()
            
            cv2.circle(imshow, (int(self.tip_pos_px[0]), int(self.tip_pos_px[1])), 10, (255, 0, 0), 2)

            self.show_frame(imshow)  # Show the frame in the main window
            self.update_idletasks()
            self.update()

            if self.key_pressed == 'Return':  # Enter key
                if print_all: print("Tip pixels: ", self.tip_pos_px)
                self.key_pressed = None
                break
            
            elif self.key_pressed is not None:
                self.tip_px_calibration(self.key_pressed)
                self.key_pressed = None


        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Tip pixel position Calibrated")
        self.message_box.see(tk.END)
        self.update_idletasks() 

        
        
        self.move_xyz(x=220, y=220, go_safe_height=True)
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        #cv2.destroyAllWindows()
        self.camera_feed_label.destroy()
        self.camera_feed_frame.destroy()
        
        self.key_pressed = None
        self.message_box.delete('1.0', tk.END)
        self.update_idletasks()  # Force GUI update

        self.tip_calibration_done = True


    def tip_px_calibration(self, key):
        incr = 1

        if key == "Right": #Right
            self.tip_pos_px[0] += incr
        elif key == "Left": #Left
            self.tip_pos_px[0] -= incr
        if key == "Up": #Up
            self.tip_pos_px[1] -= incr
        elif key == "Down": #Down
            self.tip_pos_px[1] += incr

        self.settings["Offset"]["Tip pixel position"] = self.tip_pos_px
        self.update_parameters()

    def on_key_press(self, event):
        """Handle key press events."""
        self.key_pressed = event.keysym

    def show_frame(self, frame):
        """Display the frame in the main window."""
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        photo = ImageTk.PhotoImage(image)
        self.camera_feed_label.config(image=photo)
        self.camera_feed_label.image = photo


    def offsetcalibration(self):
        #if print_all: print("This is the start of the testing function guys!!")
        # Update the message box to indicate calibration start
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Offset Calibration started")
        self.message_box.see(tk.END)
        self.update_idletasks()  # Force GUI update


        if self.is_homed == False:
            if print_all: print("You need to home the printer first")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "You need to home the printer first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return

        # self.x_firmware_limit_overwrite = -11


        if hasattr(self, 'camera_feed_frame') and self.camera_feed_frame.winfo_exists():
            self.camera_feed_frame.destroy()
            
        self.camera_feed_frame = tk.Frame(self.tabControl.tab("Mode"))
        # Adjust the row and padding to lower the frame
        self.camera_feed_frame.grid(row=1, column=1, padx=10, pady=20, rowspan=10)

        # Create a label to show the camera feed within the frame
        self.camera_feed_label = tk.Label(self.camera_feed_frame)
        self.camera_feed_label.grid(row=0, column=0)

        # self.move_xyz(z = 2 * self.safe_height)
        self.move_xyz(z = self.safe_height - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        # Lower the speed for these movements
        self.anycubic.max_x_feedrate(50)
        self.anycubic.max_y_feedrate(50)

        self.move_xyz(x = -self.last_pos[0], y = -self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        
        self.anycubic.move_home()

      
        # Bind key events
        self.bind('<Key>', self.on_key_press)

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Calibrate with arrows, U and D, and press Enter to continue")
        self.message_box.see(tk.END)
        self.update_idletasks() 

        self.key_pressed = None


        self.tip_calibration() 



#################################################################################################################################
#                                                  Main process functions                                                       #
#################################################################################################################################
    
    def set_tracker(self, target_px):
        self.tracker = cv2.TrackerCSRT.create() 
        self.roi_size = 25
        self.dist_check = 5
        self.bbox = [int(target_px[0]-self.roi_size/2),int(target_px[1]-self.roi_size/2), self.roi_size, self.roi_size]
        self.tracker.init(self.frame, self.bbox)
        self.track_on = True

    def detect(self):
        if print_all: print("This is the start of the detection function!")
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Detection started")
        self.message_box.see(tk.END)
        self.update_idletasks()
        
        if self.is_homed == False:
            if print_all: print("Printer not homed yet, please home the printer first")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not homed yet, please home the printer first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        else:
            if print_all: print("Starting detection!")
            #self.detection_place = [30, 50, 65] Nope thats wrong

            # Putting on the more interesting camera feed
            self.camera_displayed_text.set("Camera 1")
            self.displayed_cameras = 1

            if hasattr(self, 'camera_feed_frame') and self.camera_feed_frame.winfo_exists():
                self.camera_feed_frame.destroy()
                
            self.camera_feed_frame = tk.Frame(self.tabControl.tab("Mode"))
            # Adjust the row and padding to lower the frame
            self.camera_feed_frame.grid(row=1, column=1, padx=10, pady=20, rowspan=10)

            # Create a label to show the camera feed within the frame
            self.camera_feed_label = tk.Label(self.camera_feed_frame)
            self.camera_feed_label.grid(row=0, column=0)


            self.petridish_pos_for_camera = [68, 128, 60]
            self.detection_place = [self.petridish_pos_for_camera[0] + self.settings["Offset"]["Camera"][0],
                                    self.petridish_pos_for_camera[1] + self.settings["Offset"]["Camera"][1],
                                    self.petridish_pos_for_camera[2] + self.settings["Offset"]["Camera"][2]] # it was just 65 before, now it can be changed during calibration (good or not?)
           


            prev_pos = self.last_pos

            # self.anycubic.max_y_feedrate(30)
            self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"])

            self.move_xyz(x=self.detection_place[0] - self.last_pos[0], y=self.detection_place[1] - self.last_pos[1], z=self.detection_place[2] - self.last_pos[2], move_button_cmd=False, go_safe_height=False)
            
            #self.move_xyz(x=self.detection_place[0], y=self.detection_place[1], z=self.detection_place[2], move_button_cmd=False, go_safe_height=False)
            #self.move_xyz(x=self.detection_place[0], y=self.detection_place[1], z=self.detection_place[2])
            #self.move_xyz(x=30, y=50, z=65)

            self.anycubic.finish_request()
            while not self.anycubic.get_finish_flag():
                pass

            # if prev_pos - self.detection_place > [1, 1, 1]:
            if (prev_pos[0] - self.detection_place[0]) ** 2 + (prev_pos[1] - self.detection_place[1]) ** 2 + (prev_pos[2] - self.detection_place[2]) ** 2 > 4:
                if print_all: print("Not at detection place yet so better wait for liquid to stabilize")
                tm.sleep(2)

            if debug:
                self.frame = cam_gear.get_cam_frame(self.stream2)
            else:
                self.frame = cam_gear.get_cam_frame(self.stream1)
            imshow = self.frame.copy()
            if debug == False:
                imshow = self.cam.undistort(imshow)
            self.show_frame(imshow)
            self.update_idletasks()
            self.update()

            # if self.last_pos != self.detection_place:
            #     if print_all: print("Not at detection place yet so better wait for liquid to stabilize")
            #     tm.sleep(6)
                #elif self.anycubic.get_finish_flag():

            self.tip_number = 1

            self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
            self.clicked_pipette.set(self.toolhead_position[self.tip_number])

            self.sample_detector = cv.create_sample_detector(self.settings["Detection"])             
                    
            if debug:
                self.frame = cam_gear.get_cam_frame(self.stream2)
                frame = cam_gear.get_cam_frame(self.stream2) 
                self.cam = cv.Camera(frame)
                self.invert = cv.invert(self.frame)
                self.mask = cv.create_mask(200, self.frame.shape[0:2], (self.frame.shape[1]//2, self.frame.shape[0]//2))
                self.intruder_detector = cv.create_intruder_detector()
            else:
                # self.frame = cam_gear.get_cam_frame(self.stream1)
                # self.invert = cv.invert(self.frame)
                self.update_cameras()


            # if print_all: print("the frame shape now is :", self.frame.shape)
            # self.frame = self.cam.undistort(self.frame)
            # if print_all: print("the frame shape after undisortion is :", self.frame.shape)
            
            # Maybe some sleep beforer selecting the same target over and over?
            # tm.sleep(0.1)

            target_px, optimal_angle = cv.detection(self)
            # target_px = cv.detect(self.frame, self.sample_detector)
            # optimal_angle = 0

            if print_all: print("Target pixel: ", target_px)
                        
            if target_px is not None:
                if print_all: print("Tissue detected")   

                # self.message_box.delete('1.0', tk.END)
                # self.message_box.insert(tk.END, "Tissue detected")
                # self.message_box.see(tk.END)
                # self.update_idletasks()

                self.set_tracker(target_px)
                self.target_pos = self.cam.cam_to_platform_space(target_px, self.detection_place)
                self.offset_check = (self.dist_check*math.sin(optimal_angle), self.dist_check*math.cos(optimal_angle))

                if debug:
                    frame = cam_gear.get_cam_frame(self.stream2)
                else:
                    frame = cam_gear.get_cam_frame(self.stream1)
                self.frame = self.cam.undistort(frame)

                imshow = self.frame.copy()

                center = (int(target_px[0]), int(target_px[1]))
                # center = self.cam.platform_space_to_cam(center, self.detection_place)

                # Draw a circle using cv2.drawMarker around the detected tissue
                imshow = cv2.drawMarker(imshow, center, (0, 255, 0), cv2.MARKER_SQUARE, 10, 2)

                # Use the mask to draw a circle around the masked area of the petridish
                imshow = cv2.circle(imshow, (self.frame.shape[1]//2, self.frame.shape[0]//2), 200, (0, 255, 0), 2)

                # imshow = cv2.drawMarker(imshow, (target_px[0], target_px[1]), 10, (0, 255, 0), 2)
                # imshow = self.cam.undistort(imshow)
                self.show_frame(imshow) 
                self.update_idletasks()
                self.update()

                # if (self.target_pos[0] - self.petridish_pos[0]) ** 2 + (self.target_pos[1] - self.petridish_pos[1]) ** 2 > self.petridish_radius ** 2 - 5:
                # What about the petridish position is in tip space ?

                # if (self.target_pos[0] + self.settings["Offset"]["Tip one"][0] - self.petridish_pos[0]) ** 2 + (self.target_pos[1] + self.settings["Offset"]["Tip one"][1] - self.petridish_pos[1]) ** 2 > self.petridish_radius ** 2 - 5:
                
                # We now do this in pixel space : 
                if (center[0] - self.frame.shape[1]//2) ** 2 + (center[1] - self.frame.shape[0]//2) ** 2 > 200 ** 2:

                    if print_all: print("Target position is outside of the petridish")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Tissue detected outside of the petridish")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    # wait 1.5s before destroying camera feed
                    if self.manual_mode:
                        tm.sleep(2)

                    self.camera_feed_label.destroy()
                    self.camera_feed_frame.destroy()

                    self.tissue_detected = False

                    return
                elif (center[0] - self.frame.shape[1]//2) ** 2 + (center[1] - self.frame.shape[0]//2) ** 2 > 200 ** 2 - 20:

                    if print_all: print("Target position is too close to the edge of the petridish")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Tissue detected close to the edge of the petridish")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    # wait 1.5s before destroying camera feed
                    if self.manual_mode:
                        tm.sleep(2)

                    self.camera_feed_label.destroy()
                    self.camera_feed_frame.destroy()

                    self.tissue_detected = False

                    return
                else:
                    if print_all: print("Target position is inside of the petridish")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Tissue detected in the petridish")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    self.tissue_detected = True
                    self.detect_attempt = 0

                out = self.frame.copy()

                if not debug:
                    macro_dir = r"Pictures/cam2"
                else:
                    macro_dir = r"Pictures/debug"
                
                if not os.path.exists(macro_dir):
                    os.makedirs(macro_dir)
                
                _, _, files = next(os.walk(macro_dir))
                file_count = len(files)
                if not debug:
                    cv2.imwrite("Pictures/cam2/successful_capture_" + str(file_count) + ".png", out)
                else:
                    cv2.imwrite("Pictures/debug/successful_capture_" + str(file_count) + ".png", out)
                
            else:
                
                self.tissue_detected = False
                self.detect_attempt += 1

                if self.detect_attempt > 1:
                    if print_all: print("No tissue detected after {} detection attempts".format(self.detect_attempt))
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "No tissue detected after {} detection attempts".format(self.detect_attempt))
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                else:
                    if print_all: print("No tissue detected")

                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "No tissue detected!")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                ##################################################################################################
                # Update the max attempts value in case it was manually changed?
                # self.max_detect_attempt = self.settings["Detection"]["Max attempts"]
                  
                ## Maybe add a bed shake to move the tissues around
                # if (not self.manual_mode) and (self.detect_attempt == self.max_detect_attempt):

                #     self.detect_attempt = 0
                #     out = self.frame.copy()
        
                #     macro_dir = r"Pictures/cam2"
                    
                #     if not os.path.exists(macro_dir):
                #         os.makedirs(macro_dir)
                    
                #     _, _, files = next(os.walk(macro_dir))
                #     file_count = len(files)
                #     cv2.imwrite("Pictures/cam2/failed_capture_" + str(file_count) + ".png", out)
                #     if print_log: logger.info('🔎 No tissue detected')
                ###################################################################################################
                # This last block is now the job of higher order functions like pick_and_place
        
        # wait 3s before destroying camera feed
        if self.manual_mode:
            tm.sleep(3)

        self.camera_feed_label.destroy()
        self.camera_feed_frame.destroy()

        #self.message_box.delete('1.0', tk.END)
        self.update_idletasks()


    def release_tracker(self):
    
        self.track_on = False
        self.success = False

        self.target_pos = None

        self.tracker = None

        # self.tracker = cv2.TrackerCSRT.create()  
        
    def check_pickup(self):
        ## check how this is done
        if print_all: print("Checking pickup function")
        # x, y, w, h = [int(i) for i in self.bbox]
        # tracker_pos = [int(x+w/2), int(y+h/2)]

        tracker_pos = self.tracker_pos

        if print_all: 
            print("Tracker position: ", tracker_pos)
            print("Tip position in pixels: ", self.tip_pos_px)
        
        # global manual_first_check
        if print_all: print("Manual first check: ", manual_first_check)

        if manual_first_check:

            if print_all: print("Manual first check started.")

            # Ask user if the pick seems successful
            if debug or (tracker_pos[0]-self.tip_pos_px[0])**2+ (tracker_pos[1]-self.tip_pos_px[1])**2 < 20**2:
                if print_all: print("Does the pick seem to be a success? (Enter/ Backspace) Automatic would say Yes!")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Does the pick seem to be a success? (Enter/ Backspace) Automatic would say Yes!")
                self.message_box.see(tk.END)
                self.update_idletasks()
            else:
                if print_all: print("Does the pick seem to be a success? (Enter/ Backspace) Automatic would say No!")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Does the pick seem to be a success? (Enter/ Backspace) Automatic would say No!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                

            # Wait for keyboard input for answer
            # Bind key events
            self.bind('<Key>', self.on_key_press)

            self.key_pressed = None
            while True:
                if self.key_pressed == 'Return':  # Enter key
                    self.key_pressed = None
                    return True

                elif self.key_pressed == 'BackSpace':  # Backspace key
                    self.key_pressed = None
                    return False
                
                self.update_idletasks()
                self.update()

        else:    
            if debug or (tracker_pos[0]-self.tip_pos_px[0])**2+ (tracker_pos[1]-self.tip_pos_px[1])**2 < 20**2:
                return True
            else:
                return False
    
   

    def delay(self, seconds):
        start_time = tm.time()
        while tm.time() - start_time < seconds:
            pass
    
    def take_picture(self):

        if self.is_homed == False:
            if print_all: print("You need to home the printer first")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "You need to home the printer first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.reference is None and self.auto_check:
            if print_all: print("You need to do a full calibration before using the automatic check")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "You need to do a full calibration before using the automatic check")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        # Move to picture position
        #dest = self.destination()
        # self.anycubic.move_axis_relative(
        #     z=self.safe_height, 
        #     f=self.settings["Speed"]["Fast speed"], 
        #     offset=self.settings["Offset"]["Tip one"]
        # )

        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"], self.settings["Speed"]["Medium speed"])

        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        if print_all: print("Moved to safe height")

        # self.dynamixel.select_tip(tip_number=2, ID=3)
        if print_all: print("the selected tip atm: ", self.tip_number)

        self.move_xyz(x=-self.last_pos[0])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        if print_all: print("Moved to picture position")
        #self.anycubic.move_home()

        
        if self.tip_number == 1:
            perfect_pose_xz = [self.picture_pos + self.settings["Offset"]["Fixed Camera"][0], self.settings["Offset"]["Calibration point"][2] + self.settings["Offset"]["Fixed Camera"][2] - self.last_pos[2]]
        elif self.tip_number == 2:
            perfect_pose_xz = [self.picture_pos + self.settings["Offset"]["Fixed Camera 2"][0], self.settings["Offset"]["Calibration point"][2] + self.settings["Offset"]["Fixed Camera 2"][2] - self.last_pos[2]]
        else:
            if print_all: print("No tip selected")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "You need to select a tip first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return False
        
        if debug == False:
            self.anycubic.set_position(x=-self.x_firmware_limit_overwrite)
        
        self.move_xyz(x=perfect_pose_xz[0], z=perfect_pose_xz[1])
        
        # self.move_xyz(x=self.picture_pos + self.settings["Offset"]["Fixed Camera"][0])
        # self.move_xyz(z=self.settings["Offset"]["Calibration point"][2] + self.settings["Offset"]["Fixed Camera"][2] - self.last_pos[2])
        
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            pass


        if print_all: print("Moved to precise fixed camera position")
        # self.pause()
        sleep(4)

        check = self.check_pickup_two()
                
        if check:
            self.move_xyz(x=-perfect_pose_xz[0], z=-perfect_pose_xz[1])
            self.anycubic.move_axis_relative(x=-self.x_firmware_limit_overwrite)
            if debug == False:
                self.anycubic.set_position(x=0)
            #self.move_xyz(x=0, y=0)
            if print_all: print("Back at home position")
            return True
        else:
            self.move_xyz(x=-perfect_pose_xz[0], z=-perfect_pose_xz[1])
            self.anycubic.move_axis_relative(x=-self.x_firmware_limit_overwrite)
            if debug == False:
                self.anycubic.set_position(x=0)
            # self.move_xyz(x=0, y=0, z=0) no need even
            if print_all: print("Back at home position")
            return False
        
    def check_pickup_two(self):

        self.camera_displayed_text.set("Camera 1")
        self.displayed_cameras = 1
        
        if hasattr(self, 'camera_feed_frame') and self.camera_feed_frame.winfo_exists():
            self.camera_feed_frame.destroy()
            
        self.camera_feed_frame = tk.Frame(self.tabControl.tab("Mode"))
        # Adjust the row and padding to lower the frame
        self.camera_feed_frame.grid(row=1, column=1, padx=10, pady=20, rowspan=10)

        # Create a label to show the camera feed within the frame
        self.camera_feed_label = tk.Label(self.camera_feed_frame)
        self.camera_feed_label.grid(row=0, column=0)

        self.frame = cam_gear.get_cam_frame(self.stream2)
        # if debug:
        #     self.frame = frame
        # else:
        #     self.frame = self.cam.undistort(frame)
        imshow = self.frame.copy()

        self.show_frame(imshow)
        self.update_idletasks()
        self.update()

        auto_good_pickup = self.auto_check_function(self.frame)
        if print_all: print("Auto check pickup result (False = Empty): ", auto_good_pickup)

        if self.auto_check:
            self.macro_frame = self.frame
            if (auto_good_pickup and not self.tissue_placed) or (not auto_good_pickup and self.tissue_placed):
                good_pickup = True
            else:
                good_pickup = False
        else:
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Press Enter if the pick/place was good, Backspace if not")
            self.message_box.see(tk.END)
            self.update_idletasks() 

            # Bind key events
            self.bind('<Key>', self.on_key_press)

            self.key_pressed = None
            good_pickup = False
            while True:
                self.macro_frame = cam_gear.get_cam_frame(self.stream2)
                # self.macro_frame = self.cam.undistort(self.macro_frame)
                self.show_frame(self.macro_frame)  # Show the frame in the main window

                if self.key_pressed == 'Return':  # Enter key
                    good_pickup = True
                    self.key_pressed = None
                    break

                elif self.key_pressed == 'BackSpace':  # Backspace key
                    self.key_pressed = None
                    break
                
                self.update_idletasks()
                self.update()

        # self.macro_frame = self.stream2.read()
        
        macro_dir = r"Pictures/macro"
        
        if not os.path.exists(macro_dir):
            os.makedirs(macro_dir)
        
        _, _, files = next(os.walk(macro_dir))
        file_count = len(files)

        if (good_pickup and not self.tissue_placed) or (not good_pickup and self.tissue_placed):
            cv2.imwrite("Pictures/macro/macro_image_" + str(file_count) + "_t.png", self.macro_frame)
        elif (good_pickup and self.tissue_placed) or (not good_pickup and not self.tissue_placed):
            cv2.imwrite("Pictures/macro/macro_image_" + str(file_count) + "_f.png", self.macro_frame)
        else:
            cv2.imwrite("Pictures/macro/macro_image_" + str(file_count) + ".png", self.macro_frame)
        
        #### Neural Network prediction from Axel:

        # res = self.NN.predict(cv2.cvtColor(self.macro_frame, cv2.COLOR_BGR2RGB).reshape(1, 480, 640, 3), verbose=0)
        # res = self.NN.predict(cv2.cvtColor(self.macro_frame, cv2.COLOR_BGR2GRAY).reshape(1, 480, 640, 1), verbose=0)
        # if print_log: logger.info(f"🔮 Prediciton results {res[0, 0]}")
        
        ## ICI IL FAUT RéACTIVER LE NEURAL NETWORK, ET ADAPTER ICI
        # while True:      

        #     # Inputs
        #     key = cv2.waitKeyEx(5)  
            
        #     if key == 13: #enter
        #         return True
        #     if key == 8: #backspace
        #         return False
            
        #     self.macro_frame = self.stream2.read() 
        #     cv2.imshow('Macro camera', self.macro_frame)
         
         
        self.camera_feed_label.destroy()
        self.camera_feed_frame.destroy()

        self.key_pressed = None

        if not self.auto_check:
            self.message_box.delete('1.0', tk.END)
            self.update_idletasks()  # Force GUI update

        return good_pickup
    
    def auto_check_function(self, img):

        size = (40, 40)
        focus_ratio = 0.5
        threshold = 12

        try:
            img1 = Image.open("Pictures/macro/reference.png")
        except:
            if print_all: print("No reference picture found")
            return False
        
        reference = np.array(img1)
        new_image = np.array(img)

        ref_image = cv2.resize(reference, size)
        new_image = cv2.resize(new_image, size)

        diff_image = cv2.absdiff(ref_image, new_image)

        h, w, _ = diff_image.shape
        focused_diff = diff_image[int(h * focus_ratio):, int(w * 0.25):int(w * 0.75)]

        # Substract the mean of the border pixels from the difference image
        left_col = focused_diff[:, 0]
        right_col = focused_diff[:, -1]
        border_pixels = np.vstack((left_col, right_col))
        border_mean = np.mean(border_pixels, axis=(0, 1))

        adjusted_diff = focused_diff - border_mean
        adjusted_diff = np.clip(adjusted_diff, 0, 255)

        avg_diff = np.mean(adjusted_diff)

        if print_log: logger.info(f"🔮 Auto check results {avg_diff}")

        #     print(f'Average difference: {avg_diff}')

        #     # Visualization for debugging
        #     plt.figure(figsize=(12, 4))
        #     plt.subplot(1, 3, 1), plt.title('Reference Image'), plt.imshow(cv2.cvtColor(ref_image, cv2.COLOR_BGR2RGB))
        #     plt.subplot(1, 3, 2), plt.title('New Image'), plt.imshow(cv2.cvtColor(new_image, cv2.COLOR_BGR2RGB))
        #     plt.subplot(1, 3, 3), plt.title('Difference Image'), plt.imshow(diff_image)
        #     plt.show()

        if avg_diff > threshold:

            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Auto check thinks that there is a tissue")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return True
        else:
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Auto check thinks that the tip is empty")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return False


    def destination(self):

        well_type = self.settings['Well']['Type']
        # Verfications for the well (can not place if none selected or if full)
        # Taken care of in the beginning of place() !

        # well_num = self.well_num

        # Some twisted naming conversions starting here:

        well_name = self.selected_wells[self.well_num]

        # Convert well_name to well_num (A1 is 1, B1 is 2, etc.)
        well_col = ord(well_name[0]) - 64
        well_row = int(well_name[1])

        total_nb_wells = {
            'TPP6': 6,
            'TPP12': 12,
            'TPP24': 24,
            'TPP48': 48,
            'NUNC48': 48,
            'FALCON48': 48,
            'Millicell plate': 6
        }.get(well_type, 12) 

        nb_wells_per_row = {
            'TPP6': 2,
            'TPP12': 3,
            'TPP24': 4,
            'TPP48': 6,
            'NUNC48': 6,
            'FALCON48': 6,
            'Millicell plate': 2
        }.get(well_type, 3)

        # Actually A1 is the furthest right and we go from right to left, so inversion:
        well_col = nb_wells_per_row - well_col + 1

        well_num = well_col - 1 + (total_nb_wells / nb_wells_per_row - well_row) * nb_wells_per_row

        if print_all: 
            print("The well is: ", well_name)
            print("It is in column: ", well_col, " and row: ", well_row)
            print("The total number of wells is: ", total_nb_wells, ",per row: ", nb_wells_per_row, " and per column: ", total_nb_wells / nb_wells_per_row)
            print("Therefore the well number is: ", well_num)

        # dim_x = self.well_dim_x
        # dim_y = self.well_dim_y
        
        # Center of first well (Nr. 0) x=139, y=114, z=110
        # Distance between wells: (189 - 139)/3 = 16.7

        # wells_per_row = self.settings["Well"]["Number of well"]
        # well_row = well_num // wells_per_row
        # well_col = well_num % wells_per_row
        
        diameter = {
            'TPP6': 33.9,
            'TPP12': 10,
            'TPP24': 15.4,
            'TPP48': 10.6,
            'NUNC48': 6.4,
            'FALCON48': 6.4,
            'Millicell plate': 10
        }.get(well_type, 10) 


        # bottom_left_well = [139, 114]
        # dist_between_wells = 100/ (nb_wells_per_row + 1)
        # Let us replace this with something that is calibreable:
        bottom_left_well = self.settings["Positions"]["Well 1"]
        dist_between_wells = self.settings["Positions"]["Well 2"][0] - self.settings["Positions"]["Well 1"][0]

        # dist_between_wells = 25 # the third one to the right is always off on the x axis ??? to be fixed

        well_pos = [bottom_left_well[0] + (well_num % 3) * dist_between_wells, bottom_left_well[1] + (well_num // 3) * dist_between_wells]

        if print_all: print("The well position will be: ", well_pos)

        radius = diameter / 4 # radius of the smaller container in the well

        if self.nb_sample < 1:
            offset = [0, 0]
        else:
            angle = (self.nb_sample) * 2 * math.pi / (self.settings["Tissues"]["Number of samples per well"] - 1)
            offset = [radius * math.cos(angle), radius * math.sin(angle)]
            # offset = [0, 0]
        if print_all: print("The added offset will be: ", offset)
        return [well_pos[0] + offset[0], well_pos[1] + offset[1]]

    def reset(self):
        
        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"], self.settings["Speed"]["Medium speed"])

        # if the pipette is outside of the petridish area:
        if (self.petridish_pos[0] - self.last_pos[0]) ** 2 + (self.petridish_pos[1] - self.last_pos[1]) ** 2 > self.petridish_radius ** 2 - 5 or self.last_pos[2] < self.settings["Position"]["Drop height"]:
            self.move_xyz(z=self.safe_height - self.last_pos[2])
            if print_all: print("Moving to safe height")

        #self.reset_pos = [30, 50, 10]
        # self.petridish_pos = [66, 130]
        self.reset_pos = [self.petridish_pos[0], self.petridish_pos[1], self.settings["Position"]["Drop height"] + 10]
        
        if print_all: print("Moving to center of petridish position")
        self.move_xyz(x=self.reset_pos[0] - self.last_pos[0], y=self.reset_pos[1] - self.last_pos[1])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        if print_all: print("Moving down to reset position")
        self.move_xyz(z=self.reset_pos[2] - self.last_pos[2])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # Empty pipette
        self.dynamixel.write_profile_velocity(self.settings["Tissues"]["Dropping speed"], ID=1)
        
        #self.pipette_1_pos = self.pipette_empty
        # self.dynamixel.write_pipette_ul(self.pipette_1_pos, ID=1)
        
        self.servo_pos[0] = self.pipette_empty
        self.dynamixel.write_pipette_ul(self.servo_pos[0], ID=1)

        # For coherence with manual controls and display values:
        # self.servo_pos[0] = self.pipette_1_pos
        self.servo_values_text[0].set(str(self.settings["Tissues"]["Dropping speed"]))
        self.display_servo_pos()

        if print_pipette_state: 
            # print("Pipette 1 position: ", self.pipette_1_pos, "Pipette 2 position: ", self.pipette_2_pos)
            print("Servo 1 position: ", self.servo_pos[0], "Servo 2 position: ", self.servo_pos[1])

        # while not self.dynamixel.pipette_is_in_position_ul(self.pipette_1_pos, ID=1):
        while not self.dynamixel.pipette_is_in_position_ul(self.servo_pos[0], ID=1):
            continue

        # Resetting sample counts and positions if necessary
        self.pick_attempt = 0
        self.detect_attempt = 0

    def empty_out(self):

        if self.is_homed == False:
            if print_all: print("Printer not homed yet, please home the printer first")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not homed yet, please home the printer first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
    
        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"], self.settings["Speed"]["Medium speed"])
        
        if (self.petridish_pos[0] - self.last_pos[0]) ** 2 + (self.petridish_pos[1] - self.last_pos[1]) ** 2 > self.petridish_radius ** 2 - 5 or self.last_pos[2] < self.settings["Position"]["Drop height"]:
            self.move_xyz(z=self.safe_height - self.last_pos[2])
            if print_all: print("Moving to safe height")

        # self.petridish_pos = [66, 130]
        self.reset_pos = [self.petridish_pos[0], self.petridish_pos[1], self.settings["Position"]["Drop height"] + 10]
        
        if print_all: print("Moving to center of petridish position")
        self.move_xyz(x=self.reset_pos[0] - self.last_pos[0], y=self.reset_pos[1] - self.last_pos[1])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        if print_all: print("Moving down to reset position")
        self.move_xyz(z=self.reset_pos[2] - self.last_pos[2])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        # Empty pipette
        self.dynamixel.write_profile_velocity(self.settings["Tissues"]["Dropping speed"], ID=1)
        
        # self.pipette_1_pos = self.pipette_empty
        # self.dynamixel.write_pipette_ul(self.pipette_1_pos, ID=1)

        self.servo_pos[0] = self.pipette_empty
        self.dynamixel.write_pipette_ul(self.servo_pos[0], ID=1)

        # For coherence with manual controls and display values:
        # self.servo_pos[0] = self.pipette_1_pos
        self.servo_values_text[0].set(str(self.settings["Tissues"]["Dropping speed"]))
        self.display_servo_pos()

        if print_pipette_state: 
            # print("Pipette 1 position: ", self.pipette_1_pos, "Pipette 2 position: ", self.pipette_2_pos)
            print("Servo 1 position: ", self.servo_pos[0], "Servo 2 position: ", self.servo_pos[1])

        # while not self.dynamixel.pipette_is_in_position_ul(self.pipette_1_pos, ID=1):
        while not self.dynamixel.pipette_is_in_position_ul(self.servo_pos[0], ID=1):
            continue

        self.message_box.delete('1.0', tk.END)
        self.update_idletasks()

        # # Resetting sample counts and positions if necessary
        # self.pick_attempt = 0
        # self.detect_attempt = 0
        # That is the difference with reset

    def remove_bubble(self):

        if self.is_homed == False:
            if print_all: print("Printer not homed yet, please home the printer first")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not homed yet, please home the printer first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"], self.settings["Speed"]["Medium speed"])

        if (self.petridish_pos[0] - self.last_pos[0]) ** 2 + (self.petridish_pos[1] - self.last_pos[1]) ** 2 > self.petridish_radius ** 2 - 5 or self.last_pos[2] < self.settings["Position"]["Drop height"]:
            self.move_xyz(z=self.safe_height - self.last_pos[2])
            if print_all: print("Moving to safe height")

        # self.petridish_pos = [66, 130]
        self.reset_pos = [self.petridish_pos[0], self.petridish_pos[1], self.settings["Position"]["Drop height"] + 10]
        
        if print_all: print("Moving to center of petridish position")
        self.move_xyz(x=self.reset_pos[0] - self.last_pos[0], y=self.reset_pos[1] - self.last_pos[1])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        if print_all: print("Moving to reset position")
        self.move_xyz(z=self.reset_pos[2] - self.last_pos[2])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        if print_all: print("Moving down to pick height, to go with the tip under water")
        self.pick_offset = 4
        self.move_xyz(z=self.settings["Position"]["Pick height"] + self.pick_offset - self.last_pos[2])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        if print_all: print("Moving back up")
        self.move_xyz(z=self.safe_height - self.last_pos[2])

    def pick(self):

        if self.is_homed == False:
            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()

            return
        
        if self.tip_calibration_done == False:
            if print_log: logger.info("Tip calibration not done yet, please do a calibration first!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            self.message_box.see(tk.END)
            self.update_idletasks()

            return

        if self.target_pos is None:
            if print_log: logger.info("There is no target tissue to pick up!")

            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "There is no target tissue to pick up")
            self.message_box.see(tk.END)
            self.update_idletasks()

            return
        
        # Check the current position of the pipette before sucking
        # if self.pipette_1_pos < self.settings["Tissues"]["Pumping Volume"]:
        if self.servo_pos[0] < self.settings["Tissues"]["Pumping Volume"]:
            # if print_all: print("The pipette can not suck any more than that, please eject or reset!")
            # if print_all: print("The pipette can not suck any more, pipette_pos is : ", self.pipette_1_pos)
            if print_all: print("The pipette can not suck any more, servo_pos is : ", self.servo_pos[0])
            if print_log: logger.info("The pipette can not suck any more than that, please eject or reset!")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not suck any more than that, please eject or reset!")
            self.message_box.see(tk.END)
            self.update_idletasks()

            return



        self.pick_offset = 4
        center = (int(self.target_pos[0]), int(self.target_pos[1]))

        if hasattr(self, 'camera_feed_frame') and self.camera_feed_frame.winfo_exists():
            self.camera_feed_frame.destroy()
            
        self.camera_feed_frame = tk.Frame(self.tabControl.tab("Mode"))
        # Adjust the row and padding to lower the frame
        self.camera_feed_frame.grid(row=1, column=1, padx=10, pady=20, rowspan=10)

        # Label to show the camera feed within the frame
        self.camera_feed_label = tk.Label(self.camera_feed_frame)
        self.camera_feed_label.grid(row=0, column=0)

        if debug:
            self.frame = cam_gear.get_cam_frame(self.stream2)
        else:
            self.frame = cam_gear.get_cam_frame(self.stream1)
        # self.frame = self.cam.undistort(frame)
        imshow = self.frame.copy()
        if debug == False:
                imshow = self.cam.undistort(imshow)
        self.show_frame(imshow)

        self.update_idletasks()
        self.update()

        # if self.manual_mode:
            # tm.sleep(3)

        if print_all: print("-----------------------------------------------")
        if print_all: print("The Target is at position : ", self.target_pos)
        if print_all: print("With offset, the target is : ", self.target_pos[0] + self.offset_check[0], self.target_pos[1] + self.offset_check[1])
        if print_all: print("The current position is : ", self.last_pos)
        if print_all: print("-----------------------------------------------")
        if print_all: print("Camera offset: ", self.settings["Offset"]["Camera"])
        if print_all: print("Tip offset: ", self.settings["Offset"]["Tip one"])
        if print_all: print("-----------------------------------------------")
        if print_all: print("The Petridish is at position : ", self.petridish_pos) 
        if print_all: print("The Petridish radius is : ", self.petridish_radius)
        if print_all: print("The offset check is : ", self.offset_check)

        # Check that this position is well inside the petridish 
        # Correction: Check that the position the tip will go to ...
        margin = 3 # with safety margins of 3
        # if (abs(self.target_pos[0] + self.offset_check[0] - self.petridish_pos[0]) < self.petridish_radius - margin and
        #     abs(self.target_pos[1] + self.offset_check[1] - self.petridish_pos[1]) < self.petridish_radius - margin and
        #     (self.target_pos[0] + self.offset_check[0] - self.petridish_pos[0]) ** 2 + (self.target_pos[1] + self.offset_check[1] - self.petridish_pos[1]) ** 2 < (self.petridish_radius - margin) ** 2
        # ):
        #     if print_all: print("!!!! Target position is outside of the petridish")
        #     self.reset()

        #     tm.sleep(2)
        #     self.camera_feed_label.destroy()
        #     self.camera_feed_frame.destroy()
        #     return
        # else:
        #     if print_all: print("!!!! Target position is inside of the petridish")

        if print_all: print("The offset check is : ", self.offset_check)
        # self.offset_check = [-1, 1]
        self.offset_check = [0, 0]
        if print_all: print("The offset check is manually changed to : ", self.offset_check)


        # CHECK NR 2 NOT REQUIRED ANYMORE
        ################################################################################################
        # Correction: Check that the position the tip will go to ...
        # if (abs(self.target_pos[0] + self.offset_check[0] + self.settings["Offset"]["Tip one"][0] - self.settings["Offset"]["Camera"][0] - self.petridish_pos[0]) > self.petridish_radius - margin and
        #     abs(self.target_pos[1] + self.offset_check[1] + self.settings["Offset"]["Tip one"][1] - self.settings["Offset"]["Camera"][1] - self.petridish_pos[1]) > self.petridish_radius - margin and
        #     (self.target_pos[0] + self.offset_check[0] + self.settings["Offset"]["Tip one"][0] - self.settings["Offset"]["Camera"][0] - self.petridish_pos[0]) ** 2 + (self.target_pos[1] + self.offset_check[1] + self.settings["Offset"]["Tip one"][1] - self.settings["Offset"]["Camera"][1] - self.petridish_pos[1]) ** 2 > (self.petridish_radius - margin) ** 2
        # ):
        #     if print_all: print("Check NR. 2 :  Target position is outside of the petridish")
        #     if print_all: print("So what is up????????????")
        #     if print_all: print("The target position is : ", self.target_pos[0] + self.offset_check[0], self.target_pos[1] + self.offset_check[1])
        #     if print_all: print("The added offsets sum up to : ",self.settings["Offset"]["Tip one"][0] - self.settings["Offset"]["Camera"][0], self.settings["Offset"]["Tip one"][1] - self.settings["Offset"]["Camera"][1])   
        #     if print_all: print("In total : ", self.target_pos[0] + self.offset_check[0] + self.settings["Offset"]["Tip one"][0] - self.settings["Offset"]["Camera"][0], self.target_pos[1] + self.offset_check[1] + self.settings["Offset"]["Tip one"][1] - self.settings["Offset"]["Camera"][1])   
        #     if print_all: print("-----------------------------------------------")
        #     if print_all: print("The petridish position is : ", self.petridish_pos)
        #     if print_all: print("The current position is : ", self.last_pos)


        #     self.reset()

        #     if self.manual_mode:
        #         tm.sleep(2)
        #     self.camera_feed_label.destroy()
        #     self.camera_feed_frame.destroy()

        #     self.tissue_picked = False

        #     return
        # else:
        #     if print_all: print("Check NR. 2 :  Target position is inside of the petridish")
        #########################################################################################################

        # Move to position
        # self.move_xyz(
        #     x=self.target_pos[0] + self.offset_check[0] - self.last_pos[0], 
        #     y=self.target_pos[1] + self.offset_check[1] - self.last_pos[1], 
        #     z=self.settings["Position"]["Pick height"] + self.pick_offset - self.last_pos[2])
        
        steps = 3
        # speeds = [10, 5, 1]
        speeds = [self.settings["Speed"]["Medium speed"]/2, self.settings["Speed"]["Medium speed"]/4, self.settings["Speed"]["Slow speed"]]
        total_height = self.settings["Position"]["Pick height"] + self.pick_offset - self.last_pos[2]
        height_steps = [total_height + 10, -8, -2]

        # Divide the movement into parts, going slower at every step (This may require some finetuning):
        for i in range(0, steps):

            if print_all:
                print("For the picking procedure, out of ", steps, " steps, we are at step ", i+1)
                print("Now going down by ", height_steps[i])

            speed = speeds[i]
            # Make the move slower
            self.set_speed(speed, speed, speed)

            # With the two offsets added :
            self.move_xyz(
                x=self.target_pos[0] + self.offset_check[0] + self.settings["Offset"]["Tip one"][0] - self.settings["Offset"]["Camera"][0] - self.last_pos[0], 
                y=self.target_pos[1] + self.offset_check[1] + self.settings["Offset"]["Tip one"][1] - self.settings["Offset"]["Camera"][1] - self.last_pos[1], 
                z=height_steps[i])


            self.anycubic.finish_request()
            while not self.anycubic.get_finish_flag():

                # self.show_frame(cam_gear.get_cam_frame(self.stream1))
                if debug:
                    self.frame = cam_gear.get_cam_frame(self.stream2)
                else:
                    self.frame = cam_gear.get_cam_frame(self.stream1)

                if print_all: print("Before undistort, the frame is : ", self.frame.shape)
                self.frame = self.cam.undistort(self.frame) # that or after???
                if print_all: print("After undistort, the frame is : ", self.frame.shape)

                imshow = self.frame.copy()
                success, self.bbox = self.tracker.update(self.frame)

                # print("Trackin Success is : ", success)

                # imshow = self.cam.undistort(imshow)

                if success:
                    # Tracking success: Draw a rectangle around the tracked object
                    if print_all: print("Tracking success")

                    x, y, w, h = [int(i) for i in self.bbox]
                    center = (int(x + w / 2), int(y + h / 2))

                    if print_all: 
                        print("Tip position in pixels:    ", self.tip_pos_px)
                        # print("Calibrated tip position would be :", self.cam.platform_space_to_cam(self.settings["Offset"]["Tip one"], self.settings["Offset"]["Camera"]) + np.array([5, -5])) # small correction   

                        print("Tissue position in pixels: ", (int(x+w/2), int(y+h/2)))
                        print("Size of the image:         ", imshow.shape)

                    cv2.circle(imshow, (int(self.tip_pos_px[0]), int(self.tip_pos_px[1])), 10, (255, 0, 0), 2)
                    # cv2.circle(imshow, (10, 10), 10, (255, 0, 0), 2)

                    cv2.circle(imshow, (center[0], center[1]), int((w+h)/4), (0, 255, 0), 2)

                else:
                    # Tracking failure
                    if print_all: print("Tracking failure detected")
                    #cv2.putText(self.frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)

                # Display the frame with tracking information
                self.show_frame(imshow)
                self.update_idletasks()
                self.update()

                if print_all: print("Tracking the tissue while moving there")
                continue
        
            if print_all: print("Moved to position")

    
        # Correction (deemed unnecessary and discontinued)

        #self.delay(0.3)
        # x, y, w, h = self.bbox
        # target_px = [int(x + w / 2), int(y + h / 2)]
        # cam_pos = (
        #     self.target_pos[0] + self.offset_check[0] - self.settings["Offset"]["Camera"][0] + self.settings["Offset"]["Tip one"][0],
        #     self.target_pos[1] + self.offset_check[1] - self.settings["Offset"]["Camera"][1] + self.settings["Offset"]["Tip one"][1],
        #     self.settings["Position"]["Pick height"] + self.pick_offset - self.settings["Offset"]["Camera"][2] + self.settings["Offset"]["Tip one"][2]
        # )
        #self.target_pos = self.cam.cam_to_platform_space(target_px, cam_pos)



        # CHECK NR 3 NOT REQUIRED ANYMORE 
        ################################################################################################
        # if (self.target_pos[0] - self.petridish_pos[0]) ** 2 + (self.target_pos[1] - self.petridish_pos[1]) ** 2 > self.petridish_radius ** 2:
        #     if print_all: print("Check NR. 3 : Target position is outside of the petridish")
        #     self.reset()
        #     self.tissue_picked = False

        #     if self.manual_mode:
        #         tm.sleep(2)
        #     self.camera_feed_label.destroy()
        #     self.camera_feed_frame.destroy()
        #     return
        # else:
        #     if print_all: print("Check NR. 3 : Target position is inside of the petridish")
        ################################################################################################

        # if debug:
        #     self.frame = cam_gear.get_cam_frame(self.stream2)
        # else:
        #     self.frame = cam_gear.get_cam_frame(self.stream1)
        # imshow = self.frame.copy()
        # center = (int(target_px[0]), int(target_px[1]))
        # # Draw a circle using cv2.drawMarker around the detected tissue
        # imshow = cv2.drawMarker(imshow, center, (0, 255, 0), cv2.MARKER_SQUARE, 10, 2)    
        # self.show_frame(imshow) 
        # self.update_idletasks()
        # self.update()

        # man_corr = [0., 1.0]
        # self.anycubic.move_axis_relative(
        #     x=self.target_pos[0] + man_corr[0], 
        #     y=self.target_pos[1] + man_corr[1], 
        #     z=self.settings["Position"]["Pick height"], 
        #     f=self.settings["Speed"]["Slow speed"], 
        #     offset=self.settings["Offset"]["Tip one"]
        # )
        # What is this man correction?

        # self.anycubic.finish_request()
        # while not self.anycubic.get_finish_flag():
        #     continue


        # Suck up the tissue
        # move_servo(self, sign, idx)
        if print_all and debug == False: print("The current position of the pipette is: ", self.dynamixel.read_position(ID = 1))
        if print_all: print("The servo_pos : ", self.servo_pos[0])
        # if print_all: print("The pipette_1_pos : ", self.pipette_1_pos)
        
        self.dynamixel.write_profile_velocity(self.settings["Tissues"]["Pumping speed"], ID=1)
       
        # For coherence with manual controls and display values:
        # self.servo_pos[0] = self.pipette_1_pos
        self.servo_values_text[0].set(str(self.settings["Tissues"]["Pumping speed"]))
        self.display_servo_pos()


        # self.pipette_1_pos -= self.settings["Tissues"]["Pumping Volume"]
        # self.dynamixel.write_pipette_ul(self.pipette_1_pos, ID=1)

        self.servo_pos[0] -= self.settings["Tissues"]["Pumping Volume"]
        self.dynamixel.write_pipette_ul(self.servo_pos[0], ID=1)

        while not self.dynamixel.pipette_is_in_position_ul(self.servo_pos[0], ID=1):
            if debug:
                self.frame = cam_gear.get_cam_frame(self.stream2)
            else:
                self.frame = cam_gear.get_cam_frame(self.stream1)

            self.frame = self.cam.undistort(self.frame) 

            imshow = self.frame.copy()
            success, self.bbox = self.tracker.update(self.frame)

            if success:
                x, y, w, h = [int(i) for i in self.bbox]
                center = (int(x + w / 2), int(y + h / 2))

                cv2.circle(imshow, (int(self.tip_pos_px[0]), int(self.tip_pos_px[1])), 10, (255, 0, 0), 2)
                cv2.circle(imshow, (center[0], center[1]), int((w+h)/4), (0, 255, 0), 2)

            self.show_frame(imshow)
            self.update_idletasks()
            self.update()            
            continue

        if print_pipette_state: 
            # print("Pipette 1 position: ", self.pipette_1_pos, "Pipette 2 position: ", self.pipette_2_pos)
            print("Servo 1 position: ", self.servo_pos[0], "Servo 2 position: ", self.servo_pos[1])

        # while not self.dynamixel.pipette_is_in_position_ul(self.pipette_1_pos, ID=1):
        #     continue
        # while self.dynamixel.read_position(ID = 1) > self.pipette_1_pos:
        #     if print_all: print("Sucking up the tissue; we are at: ", self.dynamixel.read_position(ID = 1), " instead of ", self.pipette_1_pos)   
        #     continue

        if print_all: print("Sucked up the tissue")


        # Go back to reasonable speed
        # self.anycubic.max_z_feedrate(15)
        self.set_speed(self.settings["Speed"]["Medium speed"], self.settings["Speed"]["Medium speed"], self.settings["Speed"]["Medium speed"])

        # What is this ?
        #self.move_xyz(x=self.target_pos[0] + self.offset_check[0], y=self.target_pos[1] + self.offset_check[1], z=self.settings["Position"]["Pick height"] + self.pick_offset)

        # Instead this:
        self.move_xyz(z=self.settings["Position"]["Pick height"] + self.pick_offset + 10 - self.last_pos[2])  

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            if debug:
                self.frame = cam_gear.get_cam_frame(self.stream2)
            else:
                self.frame = cam_gear.get_cam_frame(self.stream1)
            self.frame = self.cam.undistort(self.frame) 

            imshow = self.frame.copy()
            success, self.bbox = self.tracker.update(self.frame)

            if success:
                x, y, w, h = [int(i) for i in self.bbox]
                center = (int(x + w / 2), int(y + h / 2))

                cv2.circle(imshow, (int(self.tip_pos_px[0]), int(self.tip_pos_px[1])), 10, (255, 0, 0), 2)
                cv2.circle(imshow, (center[0], center[1]), int((w+h)/4), (0, 255, 0), 2)

            self.show_frame(imshow)
            self.update_idletasks()
            self.update() 
            continue
        if print_all: print("Moved up a bit")

        self.tracker_pos = center

        if self.check_pickup():
            self.release_tracker()

            #self.take_picture()
            self.pick_attempt += 1
            self.tissue_picked = True
            self.tissue_placed = False

            if print_log: logger.info("Pickup successful after attempt " + str(self.pick_attempt))
            elif print_all: print("Pickup successful after attempt " + str(self.pick_attempt))
            self.pick_attempt = 0
            self.message_box.delete('1.0', tk.END)
            self.update_idletasks()
        else:
            self.pick_attempt += 1
            self.tissue_picked = False

            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Pickup failed after attempt " + str(self.pick_attempt))
            self.message_box.see(tk.END)
            self.update_idletasks()
            if print_log: logger.info("Pickup failed after attempt " + str(self.pick_attempt))

            # self.pick()

        # wait 2s before destroying camera feed
        if self.manual_mode:
            tm.sleep(2)

        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"])

        self.camera_feed_label.destroy()
        self.camera_feed_frame.destroy()
                
        self.update_idletasks()
        self.update()

    def place(self):

        if self.is_homed == False:

            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()

            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            return
        
        if self.selected_wells == []:
            if print_log: logger.info('🚫 No well selected')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "No well selected")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 
        
        if self.well_num >= len(self.selected_wells):
            if print_log: logger.info('🚫 Selected wells are full')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Selected wells are full")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 
        
        if print_all: print("Place function started!")
        # Move to position
        dest = self.destination()

        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"])

        self.move_xyz(z= self.safe_height - self.last_pos[2]) 

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # if dest[1] > 100:
        #     self.anycubic.move_axis_relative(
        #         x=80, 
        #         y=100, 
        #         f=self.settings["Speed"]["Fast speed"], 
        #         offset=self.settings["Offset"]["Tip one"]
        #     )
        # self.anycubic.move_axis_relative(
        #     x=dest[0], 
        #     y=dest[1], 
        #     f=self.settings["Speed"]["Fast speed"], 
        #     offset=self.settings["Offset"]["Tip one"]
        # )

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Now going to well number " + str(self.selected_wells[self.well_num]))
        self.message_box.see(tk.END)
        self.update_idletasks()

        if print_all: print("Now going to well number ", self.well_num, " which is at position ", self.selected_wells[self.well_num])
        if print_all: print("We have to move ", dest[0] - self.last_pos[0], dest[1] - self.last_pos[1])
        self.move_xyz(x=dest[0] - self.last_pos[0], y=dest[1] - self.last_pos[1])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            # if print_all: print("Waiting for the printer to finish moving there")
            continue    
        
        # Go down
        if print_all: print("Going down to drop height")

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Going down to drop height")
        self.message_box.see(tk.END)
        self.update_idletasks()

        # self.anycubic.move_axis_relative(
        #     z=self.settings["Position"]["Drop height"], 
        #     f=self.settings["Speed"]["Fast speed"], 
        #     offset=self.settings["Offset"]["Tip one"]
        # )
        self.move_xyz(z=self.settings["Position"]["Drop height"] - self.last_pos[2])

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue 

        # Blow
        if print_all: print("Blowing")

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Blowing")
        self.message_box.see(tk.END)
        self.update_idletasks()

        if print_all and debug == False: print("The current position of the pipette is: ", self.dynamixel.read_position(ID = 1))
        if print_all: print("The servo_pos : ", self.servo_pos[0])
        # if print_all: print("The pipette_1_pos: ", self.pipette_1_pos)
        

        if debug:
            # self.dynamixel.write_pipette(self.pipette_1_pos / (PIPETTE_MAX[0]-PIPETTE_MIN[0]), ID=1)
            self.dynamixel.write_pipette(self.servo_pos[0] / (PIPETTE_MAX[0]-PIPETTE_MIN[0]), ID=1)
            if print_all: print(2)
            # while not self.dynamixel.pipette_is_in_position(self.pipette_1_pos / (PIPETTE_MAX[0]-PIPETTE_MIN[0]), ID=1):
            #     continue
        #elif self.pipette_1_pos < PIPETTE_MIN[0]:
        # elif self.pipette_1_pos >= 570 - self.settings["Tissues"]["Dropping volume"]:

        elif self.servo_pos[0] > 570 - self.settings["Tissues"]["Dropping volume"]:
            if print_all: print("There is not enough liquid in the pipette to drop the desired dropping volume!")
            if print_log: logger.info("There is not enough liquid in the pipette to drop the desired dropping volume!")

            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "There is not enough liquid in the pipette!")
            self.message_box.see(tk.END)
            self.update_idletasks()
        else:
            self.dynamixel.write_profile_velocity(self.settings["Tissues"]["Dropping speed"], ID=1)

            # self.pipette_1_pos += self.settings["Tissues"]["Dropping volume"]
            # self.dynamixel.write_pipette_ul(self.pipette_1_pos, ID=1)

            self.servo_pos[0] += self.settings["Tissues"]["Dropping volume"]
            self.dynamixel.write_pipette_ul(self.servo_pos[0], ID=1)
            
            # For coherence with manual controls and display values:
            # self.servo_pos[0] = self.pipette_1_pos
            self.servo_values_text[0].set(str(self.settings["Tissues"]["Dropping speed"]))
            self.display_servo_pos()

            if print_pipette_state: 
                # print("Pipette 1 position: ", self.pipette_1_pos, "Pipette 2 position: ", self.pipette_2_pos)
                print("Servo 1 position: ", self.servo_pos[0], "Servo 2 position: ", self.servo_pos[1])

            if print_all: print(3)
            # while not self.dynamixel.pipette_is_in_position_ul(self.pipette_1_pos, ID=1):
            #     continue
            # while self.dynamixel.read_pos_in_ul(ID = 1)[0] < self.pipette_1_pos:
            while self.dynamixel.read_pos_in_ul(ID = 1)[0] < self.servo_pos[0]:
                # if print_all: print("Dropping the tissue; we are at: ", self.dynamixel.read_position(ID = 1), " instead of ", self.pipette_1_pos)  
                if print_all: print("Dropping the tissue; we are at: ", self.dynamixel.read_pos_in_ul(ID = 1)[0], " instead of ", self.servo_pos[0]) 
                continue

        # Go up
        if print_all: print("Going up")

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Going up!")
        self.message_box.see(tk.END)
        self.update_idletasks()

        # self.anycubic.move_axis_relative(
        #     z=self.safe_height, 
        #     f=self.settings["Speed"]["Fast speed"], 
        #     offset=self.settings["Offset"]["Tip one"]
        # )
        self.move_xyz(z=self.safe_height)

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.tissue_placed = True

        if self.manual_mode:
            # Post placement actions (reset sample count or move to next well)
            if print_all: print("Post placement actions")
            self.nb_sample += self.settings["Tissues"]["Number of samples per pick"] # Used to be just 1 but now, multiple tissues could be placed at once
            if self.nb_sample >= self.settings["Tissues"]["Number of samples per well"]:
                self.well_num += 1
                self.nb_sample = 0
                #if self.well_num >= len(self.culture_well):
                if self.well_num >= self.settings["Well"]["Number of well"]:
                    if print_log: logger.info("All wells are completed.")

                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "All wells are completed.")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    #self.reset()
                else:
                    if print_log: logger.info("Moving to next well.")

                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Moving to next well.")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    # self.reset()
            else:
                if print_log: logger.info("Ready for next sample.")

                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Ready for next sample.")
                self.message_box.see(tk.END)
                self.update_idletasks()

                # self.reset() 
            if print_all: print("Place function ended!") 

            # Wait 2s before erasing the message 
            tm.sleep(2)

        self.message_box.delete('1.0', tk.END)
        self.update_idletasks() 

#################################################################################################################################
#                                             An additional calibration process                                                 #
#################################################################################################################################

    def tubecalibration(self):

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Tube Calibration started")
        self.message_box.see(tk.END)
        self.update_idletasks()  # Force GUI update


        if self.is_homed == False:
            if print_all: print("You need to home the printer first")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "You need to home the printer first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return

        if self.settings["Gel"]["Number of mixing tubes"] < 1:
            if print_all: print("You need to set at least 1 Mixing tube")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "You need to set at least 1 Mixing tube")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.settings["Gel"]["Number of mixing tubes"] > 6:
            if print_all: print("You can't set more than 6 Mixing tubes")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "You can't set more than 6 Mixing tubes")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        # Select pipette 2
        self.tip_number = 2
        self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
        self.clicked_pipette.set(self.toolhead_position[self.tip_number])
        
        self.move_xyz(z = self.safe_height - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.bind('<Key>', self.on_key_press)
        self.key_pressed = None

        all_tubes = ["Solution A", "Wash", "Solution B"]
        for mixing_tube_nb in range(1, 1 + int(self.settings["Gel"]["Number of mixing tubes"])):
            all_tubes.append("Mixing tube " + str(mixing_tube_nb))

        all_tubes.append("Well 1")
        all_tubes.append("Well 2")

        for tube in all_tubes:

            if tube == "Well 2":
                self.move_xyz(z = 35 - self.last_pos[2])
                self.anycubic.finish_request()
                while not self.anycubic.get_finish_flag():
                    continue
            else:
                self.move_xyz(z = self.safe_height - self.last_pos[2])
                self.anycubic.finish_request()
                while not self.anycubic.get_finish_flag():
                    continue

            self.move_xyz(x = self.settings["Positions"][tube][0] - self.last_pos[0], y = self.settings["Positions"][tube][1] - self.last_pos[1])
            self.anycubic.finish_request()
            while not self.anycubic.get_finish_flag():
                continue

            if tube == "Well 1":
                self.move_xyz(z = 35 - self.last_pos[2])
                self.anycubic.finish_request()
                while not self.anycubic.get_finish_flag():
                    continue

                if print_all: print("Is this the x, y position of the Well on the bottom left?")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Is this the x, y position of the Well on the bottom left?")
                self.message_box.see(tk.END)
                self.update_idletasks()

            else:
                if print_all: print("Is this the x, y position of the " + tube + "?")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Is this the x, y position of the " + tube + "?")
                self.message_box.see(tk.END)
                self.update_idletasks()

            while True:
                if self.key_pressed == 'Return':  # Enter key
                    if print_all: print(tube + " position saved")
                    self.key_pressed = None
                    break
                elif self.key_pressed is not None:
                    self.adjusting_tube_positions(self.key_pressed, tube)
                    self.key_pressed = None
                
                self.update_idletasks()
                self.update()
                # self.after(1000, lambda: print("We loopin"))            
        
        if print_all: print("Tube positions updated!")
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Tube positions updated!")
        self.message_box.see(tk.END)
        self.update_idletasks()

        self.current_mixing_tube = 1


    
    def adjusting_tube_positions(self, key, tube):

        incr = 1

        if key == "Right": #Right
            self.settings["Positions"][tube][0] += incr
            self.move_xyz(x = self.settings["Positions"][tube][0] - self.last_pos[0])

        elif key == "Left": #Left
            self.settings["Positions"][tube][0] -= incr
            self.move_xyz(x = self.settings["Positions"][tube][0] - self.last_pos[0])

        if key == "Up": #Forward
            self.settings["Positions"][tube][1] += incr
            self.move_xyz(y = self.settings["Positions"][tube][1] - self.last_pos[1])

        elif key == "Down": #Backward
            self.settings["Positions"][tube][1] -= incr
            self.move_xyz(y = self.settings["Positions"][tube][1] - self.last_pos[1])

        elif key == "u" or key == "U": #Up
            if print_all: print("The height is to be set in the parameters, not here!")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The height is to be set in the parameters, not here!")
            self.message_box.see(tk.END)
            self.update_idletasks()

            self.move_xyz(z=1)

        elif key == "d" or key == "D": #Down
            if print_all: print("The height is to be set in the parameters, not here!")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The height is to be set in the parameters, not here!")
            self.message_box.see(tk.END)
            self.update_idletasks()

            self.move_xyz(z=-1)

        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.update_parameters()


#################################################################################################################################
#                                              Main processes related to the gel                                                #
#################################################################################################################################

    def mix(self, volume, speed, repeats = 3):

        repeats = int(repeats)

        if self.servo_pos[1] < volume:
            if print_log: logger.info("The pipette can not suck enough, please eject!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not suck enough, please eject!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        for i in range(repeats):
            if print_all: print("Mixing number ", i+1)

            self.dynamixel.write_profile_velocity(speed, ID=2)
            self.servo_pos[1] -= volume
            self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)

            if debug == False:
                while self.dynamixel.read_pos_in_ul(ID = 2)[0] > self.servo_pos[1]:
                    continue

            self.dynamixel.write_profile_velocity(speed, ID=2)
            self.servo_pos[1] += volume
            self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)

            if debug == False:
                while self.dynamixel.read_pos_in_ul(ID = 2)[0] < self.servo_pos[1]:
                    continue

        if print_all: print("Mixing done")

    def prepare_gel(self):

        if self.is_homed == False:
            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.tip_calibration_done == False:
            if print_log: logger.info("Tip calibration not done yet, please do a calibration first!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        
        if self.servo_pos[1] < self.settings["Solution A"]["Solution A pumping volume"] or self.servo_pos[1] < self.settings["Solution B"]["Solution B pumping volume"]:
            if print_log: logger.info("The pipette can not take these pumping volumes!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not take these pumping volumes!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.servo_pos[1] < self.settings["Solution A"]["Purging volume"]:
            if print_log: logger.info("The pipette can not take the set purging volume!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not take the set purging volume!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.servo_pos[1] < (self.settings["Solution A"]["Solution A pumping volume"] + self.settings["Solution B"]["Solution B pumping volume"]) * self.settings["Gel"]["Proportion of mixing volume"]:
            if print_log: logger.info("The pipette can not take the set Gel-Mixing volume!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not take the set Gel-Mixing volume!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return

        if self.current_mixing_tube > self.settings["Gel"]["Number of mixing tubes"]:
            if print_log: logger.info("All mixing tubes are full! Run a tube calibration to reset the count!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "All mixing tubes are full! Run a tube calibration to reset the count!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return

        # Volumes that will be pumped:
        # - Solution A pumping volume
        # + Solution A pumping volume
        # Rinse: Solution A purging volume
        # - Solution B pumping volume
        # + Solution B pumping volume
        # Mix: (Solution B pumping volume + Solution A purging volume) * Proportion of mixing volume

        # The max volume that needs to be taken in is either:
        # Solution A pumping volume
        # Solution A purging volume
        # Solution B pumping volume
        # (Solution B pumping volume + Solution A purging volume) * Proportion of mixing volume


        # And during gel application:
        # - Gel: gel volume_per_well * len(selected_wells)
        # + Gel: gel volume_per_well * len(selected_wells)
        # Rinse: Solution A purging volume
        
        # The max volume that needs to be taken in is either:
        # gel volume_per_well * len(selected_wells)
        # Solution A purging volume


        # Select pipette 2
        self.tip_number = 2
        self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
        self.clicked_pipette.set(self.toolhead_position[self.tip_number])

        # Set the speed to fast
        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"])

        # Move to solution A
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=self.settings["Positions"]["Solution A"][0] - self.last_pos[0], y=self.settings["Positions"]["Solution A"][1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # self.move_xyz(z=self.settings["Positions"]["Solution A"][2] - self.last_pos[2])
        self.move_xyz(z=self.settings["Gel"]["Vial pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # Pump solution A
        self.dynamixel.write_profile_velocity(self.settings["Solution A"]["Solution A pumping speed"], ID=2)
        self.servo_pos[1] -= self.settings["Solution A"]["Solution A pumping volume"]
        self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)

        if print_all: print("Pumping solution A")

        if debug == False:
            while self.dynamixel.read_pos_in_ul(ID = 2)[0] > self.servo_pos[1]:
                if print_all: print("Pumping solution A; we are at: ", self.dynamixel.read_pos_in_ul(ID = 2)[0], " instead of ", self.servo_pos[1])
                continue

        if print_all: print("Solution A pumped")

        # Put A in the mixing tube:

        # Move to the Mixing tube
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=self.settings["Positions"]["Mixing tube " + str(self.current_mixing_tube)][0] - self.last_pos[0], y=self.settings["Positions"]["Mixing tube " + str(self.current_mixing_tube)][1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # self.move_xyz(z=self.settings["Positions"]["Mixing tubes"][2] - self.last_pos[2])
        self.move_xyz(z=self.settings["Gel"]["Tube pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        if print_all: print("Putting solution A into the mixing tube")

        # Put Solution A into the Mixing tube
        self.dynamixel.write_profile_velocity(self.settings["Solution A"]["Solution A dropping speed"], ID=2)
        self.servo_pos[1] += self.settings["Solution A"]["Solution A pumping volume"]
        self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)

        if debug == False:
            while self.dynamixel.read_pos_in_ul(ID = 2)[0] < self.servo_pos[1]:
                continue

        if print_all: print("Solution A in the mixing tube")

        # Move to rinsing tube
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=self.settings["Positions"]["Wash"][0] - self.last_pos[0], y=self.settings["Positions"]["Wash"][1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # self.move_xyz(z=self.settings["Positions"]["Wash"][2] - self.last_pos[2])
        self.move_xyz(z=self.settings["Gel"]["Tube pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        if print_all: print("Rinsing tube reached")

        # Rinse quickly
        self.mix(self.settings["Solution A"]["Purging volume"], self.settings["Solution A"]["Purging speed"], self.settings["Gel"]["Number of wash"])

        if print_all: print("Rinsing done")

        # Same as A for Solution B:

        # Move to solution B
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=self.settings["Positions"]["Solution B"][0] - self.last_pos[0], y=self.settings["Positions"]["Solution B"][1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # self.move_xyz(z=self.settings["Positions"]["Solution B"][2] - self.last_pos[2])
        self.move_xyz(z=self.settings["Gel"]["Vial pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # Pump solution B
        self.dynamixel.write_profile_velocity(self.settings["Solution B"]["Solution B pumping speed"], ID=2)
        self.servo_pos[1] -= self.settings["Solution B"]["Solution B pumping volume"]
        self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)
        
        if debug == False:
            while self.dynamixel.read_pos_in_ul(ID = 2)[0] > self.servo_pos[1]:
                continue


        # Put B in the mixing tube:

        # Move to the Mixing tube
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=self.settings["Positions"]["Mixing tube " + str(self.current_mixing_tube)][0] - self.last_pos[0], y=self.settings["Positions"]["Mixing tube " + str(self.current_mixing_tube)][1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # self.move_xyz(z=self.settings["Positions"]["Mixing tubes"][2] - self.last_pos[2])
        self.move_xyz(z=self.settings["Gel"]["Tube pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
        
        # Put Solution B into the Mixing tube
        self.dynamixel.write_profile_velocity(self.settings["Solution B"]["Solution B dropping speed"], ID=2)
        self.servo_pos[1] += self.settings["Solution B"]["Solution B pumping volume"]
        self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)

        if debug == False:
            while self.dynamixel.read_pos_in_ul(ID = 2)[0] < self.servo_pos[1]:
                continue

        # Mixing
        self.mix((self.settings["Solution B"]["Solution B pumping volume"] + self.settings["Solution A"]["Solution A pumping volume"]) * self.settings["Gel"]["Proportion of mixing volume"], self.settings["Solution A"]["Purging speed"], self.settings["Gel"]["Number of mix"])

        self.start_stopwatch()

        # Go back to safe height
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue



        print("Gel preparation done")
        self.gel_preparation = True
        self.current_mixing_tube += 1
        return 
    
    def apply_gel(self):

        ###################################################
        # Added parameters:
        gel_volume_per_well = self.settings["Gel"]["Gel volume per well"]
        gel_pumping_speed = self.settings["Gel"]["Gel pumping speed"]
        gel_dropping_speed = self.settings["Gel"]["Gel dropping speed"]
        ###################################################

        if self.is_homed == False:
            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.tip_calibration_done == False:
            if print_log: logger.info("Tip calibration not done yet, please do a calibration first!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.selected_wells == []:
            if print_log: logger.info('🚫 No well selected')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "No well selected")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 
        
        if self.gel_preparation == False or self.current_mixing_tube < 2:
            if print_log: logger.info('🚫 Gel not prepared')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Gel not prepared")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.well_nb_with_gel >= len(self.selected_wells):
            if print_log: logger.info('🚫 Selected wells are full with gel')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Selected wells are full with gel")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 
        
        if ((self.well_num == self.well_nb_with_gel) and (self.nb_sample != 0)) or (self.well_num > self.well_nb_with_gel):
            if print_log: logger.info('🚫 A tissue placement was performed in the selected well, select new wells!')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "A tissue placement was performed in the selected well, select new wells!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
                
        if self.servo_pos[1] < gel_volume_per_well:
            if print_log: logger.info("The pipette can not pump that much gel!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not pump that much gel!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        

        # if self.servo_pos[1] < gel_volume_per_well * len(self.selected_wells):
        #     if print_log: logger.info("The pipette can not pump that much; select less wells perhaps!")
            
        #     self.message_box.delete('1.0', tk.END)
        #     self.message_box.insert(tk.END, "The pipette can not pump that much; select less wells perhaps!")
        #     self.message_box.see(tk.END)
        #     self.update_idletasks()
        #     return
        
        if self.servo_pos[1] < self.settings["Solution A"]["Purging volume"]:
            if print_log: logger.info("The pipette can not take the set Purging volume!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not take the set Purging volume!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        # if self.nb_sample != 0 or self.well_num != 0:
        #     if print_log: logger.info("It seems like a tissue placement was performed in one of the selected wells, select new wells!")
            
        #     self.message_box.delete('1.0', tk.END)
        #     self.message_box.insert(tk.END, "It seems like a tissue placement was performed in one of the selected wells, select new wells!")
        #     self.message_box.see(tk.END)
        #     self.update_idletasks()
        #     return
        
        # Select pipette 2
        self.tip_number = 2
        self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
        self.clicked_pipette.set(self.toolhead_position[self.tip_number])

        # Set the speed to fast
        self.set_speed(self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Fast speed"], self.settings["Speed"]["Medium speed"])

        # Take gel from the mixing tube (right amount):
        # Move to the Mixing tube
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=self.settings["Positions"]["Mixing tube " + str(self.current_mixing_tube - 1)][0] - self.last_pos[0], y=self.settings["Positions"]["Mixing tube " + str(self.current_mixing_tube - 1)][1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # self.move_xyz(z=self.settings["Positions"]["Mixing tubes"][2] - self.last_pos[2])
        self.move_xyz(z=self.settings["Gel"]["Tube pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # Pump the gel
        self.dynamixel.write_profile_velocity(gel_pumping_speed, ID=2)
        # self.servo_pos[1] -= gel_volume_per_well * len(self.selected_wells)
        self.servo_pos[1] -= gel_volume_per_well
        self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)

        if debug == False:
            while self.dynamixel.read_pos_in_ul(ID = 2)[0] > self.servo_pos[1]:
                continue
        
        ############################################### OBSOLETE BECAUSE 1 GEL PER WELL

        # # Move to the first selected well (bc safety height here is higher than above the well plate)
        # dest = self.destination()
        # # Move to well
        # self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        # self.anycubic.finish_request()
        # while not self.anycubic.get_finish_flag():
        #     continue

        # self.move_xyz(x=dest[0] - self.last_pos[0], y=dest[1] - self.last_pos[1])
        # self.anycubic.finish_request()
        # while not self.anycubic.get_finish_flag():
        #     continue

        # # Place it in all selected wells
        # for well in self.selected_wells:
                
        #         dest = self.destination()
        #         self.well_num += 1
        #         # Move to well
        #         self.move_xyz(z=self.safe_height - self.last_pos[2])
        #         self.anycubic.finish_request()
        #         while not self.anycubic.get_finish_flag():
        #             continue
    
        #         self.move_xyz(x=dest[0] - self.last_pos[0], y=dest[1] - self.last_pos[1])
        #         self.anycubic.finish_request()
        #         while not self.anycubic.get_finish_flag():
        #             continue
    
        #         self.move_xyz(z=self.settings["Gel"]["Well plate pumping height"] - self.last_pos[2])
        #         self.anycubic.finish_request()
        #         while not self.anycubic.get_finish_flag():
        #             continue
    
        #         # Drop the gel
        #         self.dynamixel.write_profile_velocity(gel_dropping_speed, ID=2)
        #         self.servo_pos[1] += gel_volume_per_well
        #         self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)
    
        #         if debug == False:
        #             while self.dynamixel.read_pos_in_ul(ID = 2)[0] < self.servo_pos[1]:
        #                 continue

        # self.well_num = 0

        # ###############################################

        # Quick manoever around having to modify the dest function

        backup_well_num = self.well_num
        backup_nb_sample = self.nb_sample

        self.well_num = self.well_nb_with_gel
        self.nb_sample = 0

        dest = self.destination()

        self.well_num = backup_well_num
        self.nb_sample = backup_nb_sample

        ################################################

        # Move to well
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=dest[0] - self.last_pos[0], y=dest[1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue
    
        self.move_xyz(z=self.settings["Gel"]["Well plate pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # Drop the gel
        self.dynamixel.write_profile_velocity(gel_dropping_speed, ID=2)
        self.servo_pos[1] += gel_volume_per_well
        self.dynamixel.write_pipette_ul(self.servo_pos[1], ID=2)

        if debug == False:
            while self.dynamixel.read_pos_in_ul(ID = 2)[0] < self.servo_pos[1]:
                continue


        ###############################################

        # Rinse pipette
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        self.move_xyz(x=self.settings["Positions"]["Wash"][0] - self.last_pos[0], y=self.settings["Positions"]["Wash"][1] - self.last_pos[1])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # self.move_xyz(z=self.settings["Positions"]["Wash"][2] - self.last_pos[2])
        self.move_xyz(z=self.settings["Gel"]["Tube pumping height"] - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # Rinse quickly
        self.mix(self.settings["Solution A"]["Purging volume"], self.settings["Solution A"]["Purging speed"], self.settings["Gel"]["Number of wash"])
        
        # Go back to safe height
        self.move_xyz(z=self.safe_height + 15 - self.last_pos[2])
        self.anycubic.finish_request()
        while not self.anycubic.get_finish_flag():
            continue

        # Go to a safe location
        self.move_xyz(x=self.petridish_pos[0] - self.last_pos[0], y=self.petridish_pos[1] - self.last_pos[1])

        if print_all: print("Gel application done")
        if print_log: logger.info("Gel application done")

        # Now the same gel is not usuable again, so we reset the gel preparation flag
        self.gel_preparation = False
        self.well_nb_with_gel += 1

        return 
    
#################################################################################################################################
#                                                 High order process functions                                                  #
#################################################################################################################################
    
    def placing_loop(self):

        self.placing_attempts = 1

        if print_log: logger.info("Do you want to try placing again?")
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Do you want to try placing again?")
        self.message_box.see(tk.END)
        self.update_idletasks()
            
        continue_placing = True

        if self.auto_check:
            if self.placing_attempts >= self.settings["Detection"]["Max place attempts"]:
                continue_placing = False
            else:
                self.placing_attempts += 1
        else:    
            self.bind('<Key>', self.on_key_press)
            self.key_pressed = None

            while True:
                if self.key_pressed == 'Return':
                    self.key_pressed = None
                    break
                elif self.key_pressed == 'BackSpace':
                    self.key_pressed = None
                    continue_placing = False
                    break
                self.update_idletasks()
                self.update()
        
        if not continue_placing:
            return

        while True:
            self.place()
            if (not cam_check) or self.take_picture():
                # Post placement actions (reset sample count or move to next well)
                if print_all: print("Post placement actions")
                self.nb_sample += self.settings["Tissues"]["Number of samples per pick"] # Used to be just 1 but now, multiple tissues could be placed at once
                if self.nb_sample >= self.settings["Tissues"]["Number of samples per well"]:
                    self.well_num += 1
                    self.nb_sample = 0
                    #if self.well_num >= len(self.culture_well):
                    if self.well_num >= self.settings["Well"]["Number of well"]:
                        if print_log: logger.info("All wells are completed.")

                        self.message_box.delete('1.0', tk.END)
                        self.message_box.insert(tk.END, "All wells are completed.")
                        self.message_box.see(tk.END)
                        self.update_idletasks()

                        #self.reset()
                    else:
                        if print_log: logger.info("Moving to next well.")

                        self.message_box.delete('1.0', tk.END)
                        self.message_box.insert(tk.END, "Moving to next well.")
                        self.message_box.see(tk.END)
                        self.update_idletasks()

                        # self.reset()
                else:
                    if print_log: logger.info("Ready for next sample.")

                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Ready for next sample.")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                self.message_box.delete('1.0', tk.END)
                self.update_idletasks() 

                self.reset()
                self.placing_complete = True
                break

            else:
                continue_placing = True

                if self.auto_check:
                    if self.placing_attempts >= self.settings["Detection"]["Max place attempts"]:
                        continue_placing = False
                    else:
                        self.placing_attempts += 1
                else:
                    if print_log: logger.info("Do you want to try placing again?")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Do you want to try placing again?")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    self.bind('<Key>', self.on_key_press)
                    self.key_pressed = None

                    while True:
                        if self.key_pressed == 'Return':
                            self.key_pressed = None
                            break
                        elif self.key_pressed == 'BackSpace':
                            self.key_pressed = None
                            continue_placing = False
                            break
                        self.update_idletasks()
                        self.update()
                
                if not continue_placing:
                    break

    def pick_and_place(self):

        if self.is_homed == False:
            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.tip_calibration_done == False:
            if print_log: logger.info("Tip calibration not done yet, please do a calibration first!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.selected_wells == []:
            if print_log: logger.info('🚫 No well selected')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "No well selected")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 
        
        if self.well_num >= len(self.selected_wells):
            if print_log: logger.info('🚫 Selected wells are full')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Selected wells are full")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 
        
        if print_pipette_state: 
            # print("Pipette 1 position: ", self.pipette_1_pos, "Pipette 2 position: ", self.pipette_2_pos)
            print("Servo 1 position: ", self.servo_pos[0], "Servo 2 position: ", self.servo_pos[1])

        # if self.pipette_1_pos < self.settings["Tissues"]["Pumping Volume"]:
        if self.servo_pos[0] < self.settings["Tissues"]["Pumping Volume"]:
            if print_log: logger.info("The pipette can not suck any more than that, please eject or reset!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not suck any more than that, please eject or reset!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        self.bind('<Key>', self.on_key_press)
        self.key_pressed = None

        self.manual_mode = False

        self.tissue_detected = False
        self.tissue_picked_nb = 0
        self.placing_complete = False

        # Select the pipette 1
        self.tip_number = 1
        self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
        self.clicked_pipette.set(self.toolhead_position[self.tip_number])


        while self.placing_complete == False:
            if self.key_pressed == 'BackSpace':
                self.key_pressed = None
                # self.reset()
                break
            tm.sleep(0.5)

            if self.tissue_picked_nb >= self.settings["Tissues"]["Number of samples per pick"] or self.tissue_picked_nb == 0:
                self.reset()
                self.tissue_picked_nb = 0
            self.remove_bubble()
            self.release_tracker()
            self.tissue_detected = False

            # Shake the bed a bit
            # self.move_xyz(y=1)
            # self.move_xyz(y=-1)
            # self.move_xyz(y=1)
            # self.move_xyz(y=-1

            if print_all: print("Detecting tissue")

            self.detect()
            if self.key_pressed == 'BackSpace':
                self.key_pressed = None
                # self.reset()
                break
            if self.tissue_detected and self.target_pos is not None:
                
                self.tissue_picked = False
                # while not self.tissue_picked:
                self.pick()
                if self.key_pressed == 'BackSpace':
                    self.key_pressed = None
                    # self.reset()
                    break
                if self.tissue_picked:
                    self.tissue_picked_nb += 1
                    if self.tissue_picked_nb < self.settings["Tissues"]["Number of samples per pick"]:
                        if print_log: logger.info(str(self.tissue_picked_nb) + " samples picked out of " + str(self.settings["Tissues"]["Number of samples per pick"]) + " for full pick.")
                        self.message_box.delete('1.0', tk.END)
                        self.message_box.insert(tk.END, str(self.tissue_picked_nb) + " samples placed out of " + str(self.settings["Tissues"]["Number of samples per pick"]) + " for full pick.")
                        self.message_box.see(tk.END)
                        self.update_idletasks()

                    elif (not cam_check) or self.take_picture():
                        if self.key_pressed == 'BackSpace':
                            self.key_pressed = None
                            # self.reset()
                            break
                        self.place()
                        if self.key_pressed == 'BackSpace':
                            self.key_pressed = None
                            # self.reset()
                            break
                        if (not cam_check) or self.take_picture():
                            
                            # Post placement actions (reset sample count or move to next well)
                            if print_all: print("Post placement actions")
                            self.nb_sample += self.settings["Tissues"]["Number of samples per pick"] # Used to be just 1 but now, multiple tissues could be placed at once
                            if self.nb_sample >= self.settings["Tissues"]["Number of samples per well"]:
                                self.well_num += 1
                                self.nb_sample = 0
                                #if self.well_num >= len(self.culture_well):
                                if self.well_num >= self.settings["Well"]["Number of well"]:
                                    if print_log: logger.info("All wells are completed.")

                                    self.message_box.delete('1.0', tk.END)
                                    self.message_box.insert(tk.END, "All wells are completed.")
                                    self.message_box.see(tk.END)
                                    self.update_idletasks()

                                    #self.reset()
                                else:
                                    if print_log: logger.info("Moving to next well.")

                                    self.message_box.delete('1.0', tk.END)
                                    self.message_box.insert(tk.END, "Moving to next well.")
                                    self.message_box.see(tk.END)
                                    self.update_idletasks()

                                    # self.reset()
                            else:
                                if print_log: logger.info("Ready for next sample.")

                                self.message_box.delete('1.0', tk.END)
                                self.message_box.insert(tk.END, "Ready for next sample.")
                                self.message_box.see(tk.END)
                                self.update_idletasks()

                            self.message_box.delete('1.0', tk.END)
                            self.update_idletasks() 


                            if self.key_pressed == 'BackSpace':
                                self.key_pressed = None
                                # self.reset()
                                break
                            self.reset()
                            self.placing_complete = True
                            break
                        else:
                            if self.key_pressed == 'BackSpace':
                                self.key_pressed = None
                                # self.reset()
                                break

                            # print("What should be done here? Try placing again? Multiple tries? Reset? TBD")
                                
                            self.placing_loop()
                            # self.reset()
                            # self.release_tracker()
                            # self.tissue_detected = False
                    # else:
                    #     self.reset()
                    #     self.release_tracker()
                    #     self.tissue_detected = False
                # else:
                #     self.reset()
                #     self.release_tracker()
                #     self.tissue_detected = False
                
                # TO ADD MAX PICK ATTEMPTS ETC (code already in pick function)
                # if self.detect_attempt >= self.settings["Detection"]["Max attempts"]:
                #     if print_log: logger.info("Max detection attempts reached.")
                    
                #     self.message_box.delete('1.0', tk.END)
                #     self.message_box.insert(tk.END, "Max detection attempts reached.")
                #     self.message_box.see(tk.END)
                #     self.update_idletasks()
                #     self.update()
                #     self.tissue_detected = False
                #     placing_complete = True

        self.manual_mode = True

        if self.placing_complete:
            if print_log: logger.info("Pick and Place complete!")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Pick and Place complete!")
            self.message_box.see(tk.END)
            self.update_idletasks()

        else:
            if print_log: logger.info("Pick and Place interrupted!")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Pick and Place interrupted!")
            self.message_box.see(tk.END)
            self.update_idletasks()

        self.camera_feed_label.destroy()
        self.camera_feed_frame.destroy()
                
        self.update_idletasks()
        self.update()

    def run_all(self):

        if self.is_homed == False:
            if print_log: logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.tip_calibration_done == False:
            if print_log: logger.info("Tip calibration not done yet, please do a calibration first!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.selected_wells == []:
            if print_log: logger.info('🚫 No well selected')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "No well selected")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 
        
        if self.well_num >= len(self.selected_wells):
            if print_log: logger.info('🚫 Selected wells are full')
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Selected wells are full")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return 

        # if self.pipette_1_pos < self.settings["Tissues"]["Pumping Volume"]:
        if self.servo_pos[0] < self.settings["Tissues"]["Pumping Volume"]:
            if print_log: logger.info("The pipette can not suck, so it will empty first!")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "The pipette can not suck, so it will empty first!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            self.reset()

        # In case gel preparation is part of the full process
        gel_volume_per_well = self.settings["Gel"]["Gel volume per well"]
        # global gel_prep
        if self.settings["Tissues"]["Number of samples per pick"] <= 1 and gel_prep:
            
            if self.servo_pos[1] < self.settings["Solution A"]["Solution A pumping volume"] or self.servo_pos[1] < self.settings["Solution B"]["Solution B pumping volume"]:
                if print_log: logger.info("The pipette can not take these pumping volumes!")
                
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "The pipette can not take these pumping volumes!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return
            
            if self.servo_pos[1] < self.settings["Solution A"]["Purging volume"]:
                if print_log: logger.info("The pipette can not take the set purging volume!")
                
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "The pipette can not take the set purging volume!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return
            
            if self.servo_pos[1] < (self.settings["Solution A"]["Solution A pumping volume"] + self.settings["Solution B"]["Solution B pumping volume"]) * self.settings["Gel"]["Proportion of mixing volume"]:
                if print_log: logger.info("The pipette can not take the set Gel-Mixing volume!")
                
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "The pipette can not take the set Gel-Mixing volume!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return

            if self.settings["Gel"]["Number of mixing tubes"] - self.current_mixing_tube < self.settings["Well"]["Number of well"] - self.well_num - 1:
                if print_log: logger.info("Not enough mixing tubes left for the selected wells!")
                
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Not enough mixing tubes left for the selected wells!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return

            # if self.servo_pos[1] < gel_volume_per_well * len(self.selected_wells):
            #     if print_log: logger.info("The pipette can not pump that much; select less wells perhaps!")
                
            #     self.message_box.delete('1.0', tk.END)
            #     self.message_box.insert(tk.END, "The pipette can not pump that much; select less wells perhaps!")
            #     self.message_box.see(tk.END)
            #     self.update_idletasks()
            #     return
            
            # if self.nb_sample != 0 or self.well_num != 0:
            #     if print_log: logger.info("It seems like a tissue placement was performed in one of the selected wells, select new wells!")
                
            #     self.message_box.delete('1.0', tk.END)
            #     self.message_box.insert(tk.END, "It seems like a tissue placement was performed in one of the selected wells, select new wells!")
            #     self.message_box.see(tk.END)
            #     self.update_idletasks()
            #     return

            if self.settings["Gel"]["Number of mixing tubes"] < 1:
                if print_all: print("You need to set at least 1 Mixing tube")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "You need to set at least 1 Mixing tube")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return
            
            if self.settings["Gel"]["Number of mixing tubes"] > 6:
                if print_all: print("You can't set more than 6 Mixing tubes")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "You can't set more than 6 Mixing tubes")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return
            
            if self.current_mixing_tube > self.settings["Gel"]["Number of mixing tubes"]:
                if print_log: logger.info("All mixing tubes are full! Run a tube calibration to reset the count!")
                
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "All mixing tubes are full! Run a tube calibration to reset the count!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return
            
            if self.well_nb_with_gel >= len(self.selected_wells):
                if print_log: logger.info('🚫 Selected wells are full with gel')
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Selected wells are full with gel")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return 
            
            if ((self.well_num == self.well_nb_with_gel) and (self.nb_sample != 0)) or (self.well_num > self.well_nb_with_gel):
                if print_log: logger.info('🚫 A tissue placement was performed in the selected well, select new wells!')
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "A tissue placement was performed in the selected well, select new wells!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return

            if self.servo_pos[1] < gel_volume_per_well:
                if print_log: logger.info("The pipette can not pump that much gel!")
                
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "The pipette can not pump that much gel!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return

        self.manual_mode = False

        self.bind('<Key>', self.on_key_press)
        self.key_pressed = None

        # global gel_prep
        if self.settings["Tissues"]["Number of samples per pick"] <= 1 and gel_prep:
            
            self.prepare_gel()

            if self.key_pressed == 'BackSpace':
                self.key_pressed = None
                if print_log: logger.info("Run all interrupted!")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Run all interrupted!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return

            self.apply_gel()

            if self.key_pressed == 'BackSpace':
                self.key_pressed = None
                if print_log: logger.info("Run all interrupted!")
                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Run all interrupted!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                return

        # while self.well_num < self.settings["Well"]["Number of well"]:
        while self.well_num < len(self.selected_wells):
            # global gel_prep
            if (self.well_num >= self.well_nb_with_gel) and gel_prep and (self.settings["Tissues"]["Number of samples per pick"] <= 1):
                
                self.prepare_gel()

                if self.key_pressed == 'BackSpace':
                    self.key_pressed = None
                    if print_log: logger.info("Run all interrupted!")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Run all interrupted!")
                    self.message_box.see(tk.END)
                    self.update_idletasks()
                    return

                self.apply_gel()

                if self.key_pressed == 'BackSpace':
                    self.key_pressed = None
                    if print_log: logger.info("Run all interrupted!")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Run all interrupted!")
                    self.message_box.see(tk.END)
                    self.update_idletasks()
                    return
            
            self.pick_and_place()

            if self.placing_complete == False:
                break

            if print_log: logger.info("Number of samples placed: " + str(self.well_num * self.settings["Tissues"]["Number of samples per well"] + self.nb_sample))
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Number of samples placed: " + str(self.well_num * self.settings["Tissues"]["Number of samples per well"] + self.nb_sample))
            self.message_box.see(tk.END)
            self.update_idletasks()
        
        self.manual_mode = True

        if self.placing_complete == False:
            if print_log: logger.info("Run all interrupted!")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Run all interrupted!")
            self.message_box.see(tk.END)
            self.update_idletasks()
        else:
            if print_log: logger.info("Run all is completed! Total number of samples placed: " + str(self.well_num * self.settings["Tissues"]["Number of samples per well"] + self.nb_sample))    
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Run all is completed! Total number of samples placed: " + str(self.well_num * self.settings["Tissues"]["Number of samples per well"] + self.nb_sample))
            self.message_box.see(tk.END)
            self.update_idletasks()


#################################################################################################################################
#                                                      Main and first function                                                  #
#################################################################################################################################


    def first_function(self):
        if print_all: print("This is the start of the testing function!")
        
        # self.detect()
        # self.offsetcalibration()
        

        # For Convinience
        if skip_calibration:
            self.move_home()
            self.tip_calibration_done = True

        # self.run_all()

        if print_all: print("This is the end of the testing function!")

if __name__ == "__main__":
    window = MyWindow()
    
    window.add_function_to_buffer(window.first_function())

    ## Equivalent to window.mainloop()
    while window.isOpen:
        window.update_cameras()
        window.execute_function_from_buffer()   
        window.update()
        window.update_idletasks()
        


        