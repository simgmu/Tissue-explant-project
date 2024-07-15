import tkinter as tk                     
from tkinter import ttk 
import json
import customtkinter as ctk
import numpy as np
import math
import os
import time as tm
from loguru import logger
    
from Platform.Communication.ports_gestion import * 
import Platform.computer_vision as cv
from PIL import Image, ImageTk
import Developpement.Cam_gear as cam_gear
import cv2


debug = True

if debug:
    from Platform.Communication.fake_communication import * 
else:
    from Platform.Communication.dynamixel_controller import *
    from Platform.Communication.printer_communications import * 
    import Developpement.Cam_gear as cam_gear
    

### ATTENTION AU OFFSET  !!!

SETTINGS = "TEST.json"
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
            print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in X-UP")
            self.target_class.move_xyz(x=self.target_class.xyz_step_buttons.get(), y=0, z=0)
        else:
            print(" Printer not homed yet, please home the printer first")


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
                print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Z-UP")
                self.target_class.move_xyz(x=0, y=0, z=self.target_class.xyz_step_buttons.get())
            else:
                print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Y-UP")
                self.target_class.move_xyz(x=0, y=self.target_class.xyz_step_buttons.get(), z=0)
        else:
            print(" Printer not homed yet, please home the printer first")
            

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
            print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in X-DOWN")
            self.target_class.move_xyz(x=-self.target_class.xyz_step_buttons.get(), y=0, z=0)
        else:
            print(" Printer not homed yet, please home the printer first")


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
                print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Z-DOWN")
                self.target_class.move_xyz(x=0, y=0, z=-self.target_class.xyz_step_buttons.get())
            else:
                print("Moving  "+str(self.target_class.xyz_step_buttons.get()), " in Y-DOWN")
                self.target_class.move_xyz(x=0, y=-self.target_class.xyz_step_buttons.get(), z=0)
        else:
            print(" Printer not homed yet, please home the printer first")
            

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
        print("home position")
        self.target_class.move_home()
        
        
class MyWindow(ctk.CTk):
    def __init__(self): 
        super().__init__()
        # eventuellement ajouter des class pour les boutons, pour mieux gerer les scenarios, dui gnre les well plate button
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
        '''
        I created this because in some instance, I needed the variable to be created beforehand. At first, it was to make sure 
        I could delete something, even if it didn't exist, but it turns out I misused the winfo_exists() method.
        Before I realized this, I decided to pre create everything here, in order to avoid potential issues...
        Now, this also serves as a dictionnary of variables (somewhat incomplete, as I didn't properly update this function once
        I realized my mistake). But still, it is extremely useful. It's just that we can potentially remove half of the function
        and it would still work.
        '''
        self.is_homed = False
        self.tip_calibration_done = False
        self.manual_mode = True
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
        self.debug = debug
        self.well_num = 0
        self.nb_sample = 0
        self.nb_samples_per_well = 0
        self.pipette_1_pos = 0
        self.pipette_2_pos = 0 
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
        
        
        self.safe_height        = 55
        
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
        self.pipette_empty  = 570 ## this variable shouldn't exists! We should calibrate with the value inside write_pipette_ul
        self.pipette_max_ul = 680 # ONLY FOR PURGING
        self.servo_pos      = [self.pipette_empty, self.pipette_empty, 30]
        
        self.buffer_moves = []
                
                
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
                self.tip_number = 0
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
        
            
    def set_tabs(self, i): # maybe there's a cleaner way of doing this
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
        print("test")
        
    
    #### Functions related to the mode tab ####            
    def set_tab_mode(self):
        self.mode_control_frame = ctk.CTkFrame(self.tabControl.tab("Mode"))
        self.mode_control_frame.place(relx=0.1, rely=0.1)
        self.calibration_buttons()
        self.step_buttons()

        # Message text box
        self.message_box = ctk.CTkTextbox(self.mode_control_frame, width=400, height=30)
        self.message_box.grid(row=2, columnspan=2)
        
        self.camera_mode_frame = ctk.CTkFrame(self.tabControl.tab("Mode"))
        self.camera_mode_frame.place(relx=0.8, rely=0.7, anchor=tk.CENTER)
        self.mode_camera_button = ctk.CTkButton(self.camera_mode_frame, 
                                             textvariable=self.camera_displayed_text,
                                             command= self.show_camera_control)
        self.mode_camera_button.grid(row=0)
        
        self.camera_feed_mode = ctk.CTkLabel(self.camera_mode_frame, text = "", width=480, height=270)
        self.camera_feed_mode.grid(row=1)  
        
        
    def calibration_buttons(self):
        
        self.calibration_frame = ctk.CTkFrame(self.mode_control_frame)
        self.calibration_frame.grid(row = 0, column = 0, padx = 10)
        
        self.calibration_label = ctk.CTkLabel(self.calibration_frame, text="Calibrations:")
        self.calibration_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.full_calibration_button = ctk.CTkButton(self.calibration_frame, text="Full calibration", command=self.fullcalibration)  
        self.full_calibration_button.grid(row=1, column=0, padx=10, pady=10)
        
        self.xyz_homing_button = ctk.CTkButton(self.calibration_frame, text="XYZ homing", command=self.move_home)
        self.xyz_homing_button.grid(row=3, column=0, padx=10, pady=10)
        
        self.calibrate_offset_button = ctk.CTkButton(self.calibration_frame, text="Calibrate offsets", command=self.offsetcalibration) 
        self.calibrate_offset_button.grid(row=2, column=0, padx=10, pady=10)

        self.take_picture_button = ctk.CTkButton(self.calibration_frame, text="Fixed Camera", command=self.take_picture) 
        self.take_picture_button.grid(row=4, column=0, padx=10, pady=10)

        
    
    def step_buttons(self):
        self.steps_frame = ctk.CTkFrame(self.mode_control_frame)
        self.steps_frame.grid(row = 0, column = 1, padx = 10)
        
        self.steps_label = ctk.CTkLabel(self.steps_frame, text="Steps:")
        self.steps_label.grid(row=0, column=0, padx=10, pady=10)
        
        self.run_all_button = ctk.CTkButton(self.steps_frame, text="Run all", command=self.run_all)
        self.run_all_button.grid(row=1, column=0, padx=10, pady=10)
        
        self.prep_gel_button = ctk.CTkButton(self.steps_frame, text="Prepare gel", command=self.debug_function)
        self.prep_gel_button.grid(row=2, column=0, padx=10, pady=10)

        self.prep_gel_button = ctk.CTkButton(self.steps_frame, text="Apply gel", command=self.debug_function)
        self.prep_gel_button.grid(row=3, column=0, padx=10, pady=10)

        self.detect_button = ctk.CTkButton(self.steps_frame, text="Detect", command=self.detect)
        self.detect_button.grid(row=4, column=0, padx=10, pady=10)
        
        self.pick_button = ctk.CTkButton(self.steps_frame, text="Pick", command=self.pick)
        self.pick_button.grid(row=5, column=0, padx=10, pady=10)

        self.pnp_button = ctk.CTkButton(self.steps_frame, text="Place", command=self.place)
        self.pnp_button.grid(row=6, column=0, padx=10, pady=10)

        self.pnp_button = ctk.CTkButton(self.steps_frame, text="Pick and place", command=self.pick_and_place)
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
            print("the frame shape initially is :", self.frame.shape)
            self.invert = cv.invert(self.frame)
            self.mask = cv.create_mask(200, self.frame.shape[0:2], (self.frame.shape[1]//2, self.frame.shape[0]//2))
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
        img = cv2.resize(img, (320, 180))
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
        self.param_tree_frame.place(relx = 0.1, rely=0.1, relheight=0.8, relwidth=0.5)
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
   
   
    def check_param_value(self, val):
        val_return = True
        try:
            val_return = round(float(val), 2)
        except:
            print("Incorrect input. Please write a number here. If your number uses a comma, please replace it with '.'")
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
        
        self.text_remaining_wells = ctk.StringVar() # shows how many more wells you can still select
        self.remaining_wells = ctk.CTkLabel(self.tabControl.tab("Well plate"),
                                        textvariable=self.text_remaining_wells,
                                        width=100,
                                        wraplength=500)
        self.remaining_wells.place(relx=0.3, rely=0.55, anchor=tk.CENTER)
        
        
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
    
            
    def show_wells(self, click):
        
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
                                                   text=self.label_col[i]+self.label_row[j], 
                                                   width=5, 
                                                   relief="raised", 
                                                   command=lambda idx = index: (self.toggle_well(idx, self.layout[well_id]))))
                self.well_buttons[index].grid(column=i, row=j) 
                index = index + 1
                
    
    def toggle_well(self, index, layout):
        button = self.well_buttons[index]
        temp = self.label_row[index%layout[1]]
        temp2 = self.label_col[index//layout[1]]
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
            self.remaining_wells.configure(text_color="")
        else:
            self.text_remaining_wells.set("You can still select "+str(6-len(self.selected_wells))+" wells")
            self.remaining_wells.configure(text_color="black")
        
        
    def save_well_settings(self):
        self.settings["Well"]["Type"] = self.clicked_well.get()
        self.settings["Well"]["Number of well"] = len(self.selected_wells)
        for i in range(len(self.selected_wells)):
            self.settings["Well"][f"Culture {i+1}"] = self.selected_wells[i]    
        with open('TEST.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
        self.update_parameters()

    
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
        
    
    def select_tip(self, value):
        # make it so it also changes the offset maybe, both internally and visually(GUI)
        self.move_xyz(go_safe_height=True) 

        self.tip_number = self.toolhead_position.index(value)
        print("Selected tip number is {}".format(value))
        print(" This corresponds to number ", self.toolhead_position.index(value))

        self.dynamixel.select_tip(tip_number=self.toolhead_position.index(value), ID=3)     
        
        
    def select_offset(self, value):
        self.offset = self.settings["Offset"][value]  
        ### ajouter un wait peut etre pour pas qu'il le fasse en même temps
        self.move_xyz(go_safe_height=True) 
      
        
    def move_home(self):
        
        self.anycubic.homing()
        self.anycubic.max_x_feedrate(300)
        self.anycubic.max_y_feedrate(300)
        self.anycubic.max_z_feedrate(25)   
        self.anycubic.move_home()
        
        self.is_homed = True    
        [self.coord_value_text[i].set(0) for i in range(3)]
        [self.coord_value[i].configure(state='normal') for i in range(3)]

        print("Homing complete")
        
        
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
                    print("You need to enter XYZ coords as value, with '.', not letters or other symbols")
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
            
        print("Setting position to X={}, Y={}, Z={}".format(x,y,z))
        print("Offset is {}".format(self.offset))
        
        #### Il faudrait coder ca pour qu'il aille dynamiquement dans le négatif, en prennant compte de l'offset, pour un code plus clean+
         # ATTENTION DIFFERENCE BETWEEN STEPS AND MOVE COMMAND !!
         # When we do a move command, currently, we lose the last position, 
         # which is important for setting the correct negativ pos
         # also, once this is done, there may be a bug, when changing the offset, while in negative
        if (x < -offset[0]) or (self.last_pos[0] < -offset[0]):
            delta = round(x - self.last_pos[0],2)
            # print(delta)
            if delta < 0: # we go further into the negative
                self.anycubic.set_position(x = -delta) 
            elif x < 0: # we go in positive direction, but still in negative
                self.anycubic.set_position(x = -delta) # I DON'T UNDERSTAND WHY THIS WORKS, BUT IT WORKS
            else: # we return to positive domain
                self.anycubic.set_position(x = self.last_pos[0])
            
        print("offset is {}".format(offset))
        print("x is {}".format(x))
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
        # self.documentation_frame = tk.Frame(self.tab[self.tabs_name.index("Documentation")])
        self.documentation_frame = tk.Frame(self.tabControl.tab("Documentation"))
        self.documentation_frame.pack(expand=True, fill ='both')
        
        self.doc_text = tk.Text(self.documentation_frame, width=100, height=100)
        self.doc_text.pack(expand=True, fill ='both')
        self.documentation_text = '''test, test
        test'''
        self.doc_text.insert(tk.END, self.documentation_text)
        self.doc_text.configure(state='disabled')
        self.doc_text.configure(relief="flat")
     
               
    def close_window(self):  
        with open("TEST.json", "w") as jsonFile:
            json.dump(self.settings, jsonFile, indent=4)
        try :
            self.stream2.stop()
        except:
            pass
        try:
            self.stream1.stop()
        except:
            pass
        self.isOpen = False
        
    def calibration_process(self, key, offset):
        
        # print("Key pressed is {}".format(key))
        # print(key)

        incr = 0.1
                
        # if key == 2424832: #Right
        if key == "Right": #Right
            offset[0] += incr
            print("Left right offset is: ", offset[0])
            self.anycubic.move_axis_relative(x=self.settings["Offset"]["Calibration point"][0], 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)
            
        # elif key == 2555904: #Left
        elif key == "Left": #Left
            offset[0] -= incr
            print("Left right offset is: ", offset[0])
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
        
        # print("Key pressed is {}".format(key))
        # print(key)

        incr = 0.1
                
        # if key == 2424832: #Right
        if key == "Right": #Right
            offset[0] += incr
            print("Left right offset is: ", offset[0])
            self.anycubic.move_axis_relative(x=self.picture_pos, 
                                            y=self.settings["Offset"]["Calibration point"][1], 
                                            z=self.settings["Offset"]["Calibration point"][2], offset=offset)
            
        # elif key == 2555904: #Left
        elif key == "Left": #Left
            offset[0] -= incr
            print("Left right offset is: ", offset[0])
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
        # self.x_firmware_limit_overwrite = -9
        # self.x_firmware_limit_overwrite = -11

        # # Create a frame to show the camera feed
        # if not hasattr(self, 'camera_feed_frame'):
        #     self.camera_feed_frame = tk.Frame(self.tabControl.tab("Mode"))
        #     self.camera_feed_frame.grid(row=1, column=1, padx=10, pady=20, rowspan=10)

        # # Create a label to show the camera feed within the frame
        # if not hasattr(self, 'camera_feed_label'):
        #     self.camera_feed_label = tk.Label(self.camera_feed_frame)
        #     self.camera_feed_label.grid(row=0, column=0)

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

        self.key_pressed = None
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

        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Fixed Camera Calibrated")
        self.message_box.see(tk.END)
        self.update_idletasks() 

        # Same for the second pipette
        self.dynamixel.select_tip(tip_number=2, ID=3)

        # self.anycubic.move_axis_relative(x=0, y=self.settings["Offset"]["Calibration point"][1] - self.settings["Offset"]["Fixed Camera"][1],z=self.settings["Offset"]["Calibration point"][2]-self.settings["Offset"]["Fixed Camera"][2], offset=self.settings["Offset"]["Fixed Camera 2"])
        # self.anycubic.move_axis_relative(x=0, y=self.settings["Offset"]["Calibration point"][1], z=self.settings["Offset"]["Calibration point"][2], offset=self.settings["Offset"]["Fixed Camera 2"])
        # self.anycubic.move_axis_relative(x=self.settings["Offset"]["Fixed Camera 2"][0]-self.settings["Offset"]["Fixed Camera 2"][0],
        #                                 y=self.settings["Offset"]["Fixed Camera 2"][1]-self.settings["Offset"]["Fixed Camera 2"][1], 
        #                                 z=self.settings["Offset"]["Fixed Camera 2"][2]-self.settings["Offset"]["Fixed Camera 2"][2], 
        #                                 offset=[0,0,0])

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
                print("Offset tip one: ", self.settings["Offset"]["Tip one"])
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
                print("Offset tip two: ", self.settings["Offset"]["Tip two"])
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
            imshow = cv2.drawMarker(imshow, center, (255, 0, 0), cv2.MARKER_CROSS, markerSize, thickness)

            self.show_frame(imshow)  # Show the frame in the main window
            

            if self.key_pressed == 'Return':  # Enter key
                print("Offset cam: ", self.settings["Offset"]["Camera"])
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

        self.move_xyz(x=220, y=220, go_safe_height=True)
     
        if not debug:
            self.tip_pos_px = self.cam.platform_space_to_cam(self.settings["Offset"]["Tip one"], self.settings["Offset"]["Camera"]) + np.array([5, -5])  # small correction

        #cv2.destroyAllWindows()
        self.camera_feed_label.destroy()
        self.camera_feed_frame.destroy()
        
        self.key_pressed = None
        self.message_box.delete('1.0', tk.END)
        self.update_idletasks()  # Force GUI update

        self.tip_calibration_done = True

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
        #print("This is the start of the testing function guys!!")
        # Update the message box to indicate calibration start
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Offset Calibration started")
        self.message_box.see(tk.END)
        self.update_idletasks()  # Force GUI update


        if self.is_homed == False:
            print("You need to home the printer first")
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
    
    def set_tracker(self, target_px):
        self.tracker = cv2.TrackerCSRT.create() 
        self.roi_size = 25
        self.dist_check = 5
        self.bbox = [int(target_px[0]-self.roi_size/2),int(target_px[1]-self.roi_size/2), self.roi_size, self.roi_size]
        self.tracker.init(self.frame, self.bbox)
        self.track_on = True

    def detect(self):
        print("This is the start of the detection function!")
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Detection started")
        self.message_box.see(tk.END)
        self.update_idletasks()
        
        if self.is_homed == False:
            print("Printer not homed yet, please home the printer first")
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not homed yet, please home the printer first")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        else:
            print("Starting detection!")
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

            if debug:
                self.frame = cam_gear.get_cam_frame(self.stream2)
            else:
                self.frame = cam_gear.get_cam_frame(self.stream1)
            # self.frame = self.cam.undistort(frame)
            imshow = self.frame.copy()
            if debug == False:
                imshow = self.cam.undistort(imshow)
            self.show_frame(imshow)
            

            #self.detection_place = [80, 106, 57]
            # Because : self.petridish_pos = [66, 130] and  "Tip one": [-2.9, 4.5, -1.7] and  "Camera": [10.29, -22.5, 26.6]
            # So 66 + 2.9 + 10.29 = 80.19 and 130 - 4.5 - 22.5 = 103.5 and z we do not really care about
            # In other words, we could define the dection place as follows:
            self.petridish_pos = [66, 130]
            self.detection_place = [self.petridish_pos[0] - self.settings["Offset"]["Tip one"][0] + self.settings["Offset"]["Camera"][0],
                                    self.petridish_pos[1] - self.settings["Offset"]["Tip one"][1] + self.settings["Offset"]["Camera"][1],
                                    65]
            print("Originally 30, 50, 65, but here we have ", self.detection_place)

            ''' Look at the petridish and look for tissues to pick up'''
            #if self.sub_state == 'go to position': 
                #if self.com_state == 'not send':
                    # self.anycubic.move_axis_relative(z=self.safe_height, f=self.settings["Speed"]["Fast speed"], offset=self.settings["Offset"]["Camera"])
            #self.select_offset(value="Camera")
            self.anycubic.max_y_feedrate(30)
            self.move_xyz(x=self.detection_place[0] - self.last_pos[0], y=self.detection_place[1] - self.last_pos[1], z=self.detection_place[2] - self.last_pos[2], move_button_cmd=False, go_safe_height=False)
            
            #self.move_xyz(x=self.detection_place[0], y=self.detection_place[1], z=self.detection_place[2], move_button_cmd=False, go_safe_height=False)
            #self.move_xyz(x=self.detection_place[0], y=self.detection_place[1], z=self.detection_place[2])
            #self.move_xyz(x=30, y=50, z=65)

            self.anycubic.finish_request()
            #self.com_state = 'send'
            while not self.anycubic.get_finish_flag():
                pass

            if debug:
                self.frame = cam_gear.get_cam_frame(self.stream2)
            else:
                self.frame = cam_gear.get_cam_frame(self.stream1)
            imshow = self.frame.copy()
            if debug == False:
                imshow = self.cam.undistort(imshow)
            self.show_frame(imshow)

            # if self.last_pos != self.detection_place:
            #     print("Not at detection place yet so better wait for liquid to stabilize")
            #     tm.sleep(6)
                #elif self.anycubic.get_finish_flag():

            self.tip_number = 1
            # self.detect_attempt = 0
            # self.max_detect_attempt = 50
            self.min_radius = 15
            self.max_radius = 38
            self.petridish_radius = 45

            self.dynamixel.select_tip(tip_number=self.tip_number, ID=3)
            self.sample_detector = cv.create_sample_detector(self.settings["Detection"]) 
            #self.sub_state = 'analyse picture'
            #self.com_state = 'not send'
                    
                    
            #elif self.sub_state == 'analyse picture':
            if debug:
                self.frame = cam_gear.get_cam_frame(self.stream2)
                frame = cam_gear.get_cam_frame(self.stream2) 
                self.cam = cv.Camera(frame)
                self.invert = cv.invert(self.frame)
                self.mask = cv.create_mask(200, self.frame.shape[0:2], (self.frame.shape[1]//2, self.frame.shape[0]//2))
                self.intruder_detector = cv.create_intruder_detector()

            # print("the frame shape now is :", self.frame.shape)
            self.frame = self.cam.undistort(self.frame)
            # print("the frame shape after undisortion is :", self.frame.shape)
            
            target_px, optimal_angle = cv.detection(self)
            # target_px = cv.detect(self.frame, self.sample_detector)
            # optimal_angle = 0

            print("Target pixel: ", target_px)
                        
            if target_px is not None:
                print("Tissue detected")   

                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "Tissue detected")
                self.message_box.see(tk.END)
                self.update_idletasks()

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

                # imshow = cv2.drawMarker(imshow, (target_px[0], target_px[1]), 10, (0, 255, 0), 2)
                # imshow = self.cam.undistort(imshow)
                self.show_frame(imshow) 


                # if (self.target_pos[0] - self.petridish_pos[0]) ** 2 + (self.target_pos[1] - self.petridish_pos[1]) ** 2 > self.petridish_radius ** 2 - 5:
                # What about the petridish position is in tip space ?
                if (self.target_pos[0] + self.settings["Offset"]["Tip one"][0] - self.petridish_pos[0]) ** 2 + (self.target_pos[1] + self.settings["Offset"]["Tip one"][1] - self.petridish_pos[1]) ** 2 > self.petridish_radius ** 2 - 5:
                    print("Target position is outside of the petridish")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Tissue detected outside of the petridish")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    # wait 1.5s before destroying camera feed
                    if self.manual_mode:
                        tm.sleep(1.5)

                    self.camera_feed_label.destroy()
                    self.camera_feed_frame.destroy()

                    self.tissue_detected = False

                    return
                else:
                    print("Target position is inside of the petridish")
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "Tissue detected is inside of the petridish")
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    self.tissue_detected = True

                #self.state = 'pick'
                #self.sub_state = 'empty pipette'
                #self.com_state = 'not send'
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
                print("No tissue detected")

                self.message_box.delete('1.0', tk.END)
                self.message_box.insert(tk.END, "No tissue detected!")
                self.message_box.see(tk.END)
                self.update_idletasks()
                
                self.tissue_detected = False
                self.detect_attempt += 1

                # Update the max attempts value in case it was manually changed?
                self.max_detect_attempt = self.settings["Detection"]["Max attempts"]
                  
                ## Maybe add a bed shake to move the tissues around
                if self.detect_attempt == self.max_detect_attempt:

                    print("No tissue detected after {} attempts -> Stopping".format(self.detect_attempt))
                    self.message_box.delete('1.0', tk.END)
                    self.message_box.insert(tk.END, "No tissue detected after {} attempts -> Stopping".format(self.detect_attempt))
                    self.message_box.see(tk.END)
                    self.update_idletasks()

                    self.detect_attempt = 0
                    out = self.frame.copy()
        
                    macro_dir = r"Pictures/cam2"
                    
                    if not os.path.exists(macro_dir):
                        os.makedirs(macro_dir)
                    
                    _, _, files = next(os.walk(macro_dir))
                    file_count = len(files)
                    cv2.imwrite("Pictures/cam2/failed_capture_" + str(file_count) + ".png", out)
                    logger.info('🔎 No tissue detected')
        
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
        self.tracker = cv2.TrackerCSRT.create()  
        
    def check_pickup(self):
        ## check how this is done
        print("Checking pickup function")
        x, y, w, h = [int(i) for i in self.bbox]
        tracker_pos = [int(x+w/2), int(y+h/2)]
        
        if debug or (tracker_pos[0]-self.tip_pos_px[0])**2+ (tracker_pos[1]-self.tip_pos_px[1])**2 < 20**2:
            return True
        else:
            return False
    
   

    def delay(seconds):
        start_time = tm.time()
        while tm.time() - start_time < seconds:
            pass
    
    def take_picture(platform):

        if platform.is_homed == False:
            print("You need to home the printer first")
            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "You need to home the printer first")
            platform.message_box.see(tk.END)
            platform.update_idletasks()
            return
        
        # Move to picture position
        #dest = platform.destination()
        # platform.anycubic.move_axis_relative(
        #     z=platform.safe_height, 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        platform.move_xyz(z=platform.safe_height + 15 - platform.last_pos[2])
        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue
        print("Moved to safe height")

        # platform.dynamixel.select_tip(tip_number=2, ID=3)
        print("the selected tip atm: ", platform.tip_number)

        platform.move_xyz(x=-platform.last_pos[0])

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue
        print("Moved to picture position")
        #platform.anycubic.move_home()

        # if dest[1] > 100:
        #     platform.anycubic.move_axis_relative(
        #         x=platform.picture_pos, 
        #         y=100, 
        #         f=platform.settings["Speed"]["Fast speed"], 
        #         offset=platform.settings["Offset"]["Tip one"]
        #     )
        # else:
        #     platform.anycubic.move_axis_relative(
        #         x=platform.picture_pos, 
        #         y=dest[1], 
        #         f=platform.settings["Speed"]["Fast speed"], 
        #         offset=platform.settings["Offset"]["Tip one"]
        #     )
        # platform.x_firmware_limit_overwrite = -9

        # platform.anycubic.move_axis_relative(
        #     x=platform.picture_pos, 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )

        # platform.anycubic.move_axis_relative(x=platform.settings["Offset"]["Calibration point"][0], 
        #                                      y=platform.settings["Offset"]["Calibration point"][1],
        #                                      z=platform.settings["Offset"]["Calibration point"][2], 
        #                                      offset=platform.settings["Offset"]["Fixed Camera"])
        
        # platform.move_xyz(z=platform.settings["Offset"]["Fixed Camera"][2]-platform.last_pos[2], go_safe_height=False)
        # platform.anycubic.move_axis_relative(x=platform.settings["Offset"]["Calibration point"][0], y=platform.settings["Offset"]["Calibration point"][1]-platform.last_pos[1],z=platform.settings["Offset"]["Calibration point"][2], offset=platform.settings["Offset"]["Fixed Camera"])
        # platform.anycubic.move_axis_relative(x=platform.settings["Offset"]["Calibration point"][0], y=-platform.settings["Offset"]["Fixed Camera"][1], offset=platform.settings["Offset"]["Fixed Camera"])
        if platform.tip_number == 1:
            perfect_pose_xz = [platform.picture_pos + platform.settings["Offset"]["Fixed Camera"][0], platform.settings["Offset"]["Calibration point"][2] + platform.settings["Offset"]["Fixed Camera"][2] - platform.last_pos[2]]
        elif platform.tip_number == 2:
            perfect_pose_xz = [platform.picture_pos + platform.settings["Offset"]["Fixed Camera 2"][0], platform.settings["Offset"]["Calibration point"][2] + platform.settings["Offset"]["Fixed Camera 2"][2] - platform.last_pos[2]]
        else:
            print("No tip selected")
            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "You need to select a tip first")
            platform.message_box.see(tk.END)
            platform.update_idletasks()
            return False
        
        if debug == False:
            platform.anycubic.set_position(x=-platform.x_firmware_limit_overwrite)
        
        platform.move_xyz(x=perfect_pose_xz[0], z=perfect_pose_xz[1])
        
        # platform.move_xyz(x=platform.picture_pos + platform.settings["Offset"]["Fixed Camera"][0])
        # platform.move_xyz(z=platform.settings["Offset"]["Calibration point"][2] + platform.settings["Offset"]["Fixed Camera"][2] - platform.last_pos[2])
        
        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue
        print("Moved to precise fixed camera position")
        # platform.delay(0.5)
        # platform.pause()
        if platform.check_pickup_two():
            platform.move_xyz(x=-perfect_pose_xz[0], z=-perfect_pose_xz[1])
            platform.anycubic.move_axis_relative(x=-platform.x_firmware_limit_overwrite)
            if debug == False:
                platform.anycubic.set_position(x=0)
            #platform.move_xyz(x=0, y=0)
            print("Back at home position")
            return True
        else:
            platform.move_xyz(x=-perfect_pose_xz[0], z=-perfect_pose_xz[1])
            platform.anycubic.move_axis_relative(x=-platform.x_firmware_limit_overwrite)
            if debug == False:
                platform.anycubic.set_position(x=0)
            # platform.move_xyz(x=0, y=0, z=0) no need even
            print("Back at home position")
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

        frame = cam_gear.get_cam_frame(self.stream2)
        if debug:
            self.frame = frame
        else:
            self.frame = self.cam.undistort(frame)
        imshow = self.frame.copy()

        self.show_frame(imshow)
        
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Press Enter if the pick is good, Backspace if not")
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
        cv2.imwrite("Pictures/macro/macro_image_" + str(file_count) + ".png", self.macro_frame)
        #### The first line was the one being used. In the future, update the neural network by taking a series of picture, 
        #### and re-enable it instead of waiting for a user's confirmation
        # res = self.NN.predict(cv2.cvtColor(self.macro_frame, cv2.COLOR_BGR2RGB).reshape(1, 480, 640, 3), verbose=0)
        # res = self.NN.predict(cv2.cvtColor(self.macro_frame, cv2.COLOR_BGR2GRAY).reshape(1, 480, 640, 1), verbose=0)
        # logger.info(f"🔮 Prediciton results {res[0, 0]}")
        
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
        self.message_box.delete('1.0', tk.END)
        self.update_idletasks()  # Force GUI update

        return good_pickup

    def destination(platform):

        well_num = platform.well_num
        # dim_x = platform.well_dim_x
        # dim_y = platform.well_dim_y
        
        # Center of first well (Nr. 0) x=139, y=114, z=110
        # Distance between wells: (189 - 139)/3 = 16.7

        # wells_per_row = platform.settings["Well"]["Number of well"]
        # well_row = well_num // wells_per_row
        # well_col = well_num % wells_per_row

        dist_between_wells = 25 # the third one to the right is always off on the x axis ??? to be fixed

        well_pos = [139 + (well_num % 3) * dist_between_wells, 114 + (well_num // 3) * dist_between_wells]

        # ! THIS POSITION IS NOT CORRECT, NEED TO BE ADJUSTED ?????????????????????????????????????????
        print("The well position will be: ", well_pos)

        well_type = platform.settings['Well']['Type']
        

        diameter = {
            'TPP6': 33.9,
            'TPP12': 10,
            'TPP24': 15.4,
            'TPP48': 10.6,
            'NUNC48': 6.4,
            'FALCON48': 6.4,
            'Millicell plate': 10
        }.get(well_type, 10) 

        # radius = diameter / 4 # Why ?????????? radius = diameter / 2 no?
        radius = diameter / 2

        if platform.nb_sample < 2:
            offset = [0, 0]
        else:
            # angle = (platform.nb_sample - 1) * 2 * math.pi / (platform.settings["Well"]["Number of sample per well"] - 1)
            # offset = [radius * math.cos(angle), radius * math.sin(angle)]
            # Does not work for now!
            offset = [0, 0]
        print("The added offset will be: ", offset)
        return [well_pos[0] + offset[0], well_pos[1] + offset[1]]

    def reset(platform):
        # Move to safe height
        # platform.anycubic.move_axis_relative(
        #     z=platform.safe_height, 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        platform.move_xyz(z=platform.safe_height - platform.last_pos[2])
        print("Moving to safe height")

        #platform.reset_pos = [30, 50, 10]
        platform.petridish_pos = [66, 130]
        platform.reset_pos = [platform.petridish_pos[0], platform.petridish_pos[1], platform.settings["Position"]["Drop height"] + 10]
        # THIS POSITION IS NOT CORRECT, NEED TO BE ADJUSTED ?????????????????????????????????????????

        # platform.anycubic.move_axis_relative(
        #     x=platform.reset_pos[0], 
        #     y=platform.reset_pos[1], 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        # platform.anycubic.move_axis_relative(
        #     z=platform.reset_pos[2], 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        print("Moving to center of petridish position")
        platform.move_xyz(x=platform.reset_pos[0] - platform.last_pos[0], y=platform.reset_pos[1] - platform.last_pos[1], z=platform.reset_pos[2] - platform.last_pos[2])

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue

        # Empty pipette
        platform.dynamixel.write_profile_velocity(platform.settings["Tissues"]["Dropping speed"], ID=1)
        platform.pipette_1_pos = platform.pipette_empty
        platform.dynamixel.write_pipette_ul(platform.pipette_1_pos, ID=1)
        while not platform.dynamixel.pipette_is_in_position_ul(platform.pipette_1_pos, ID=1):
            continue

        # Resetting sample counts and positions if necessary
        platform.pick_attempt = 0
        platform.detect_attempt = 0

    def pick(platform):

        if platform.is_homed == False:
            logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            platform.message_box.see(tk.END)
            platform.update_idletasks()

            return
        
        if platform.tip_calibration_done == False:
            logger.info("Tip calibration not done yet, please do a calibration first!")
            
            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            platform.message_box.see(tk.END)
            platform.update_idletasks()

            return

        if platform.target_pos is None:
            logger.info("There is no target tissue to pick up!")

            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "There is no target tissue to pick up")
            platform.message_box.see(tk.END)
            platform.update_idletasks()

            return

        platform.pick_offset = 4
        #platform.petridish_pos = [30, 50]
        platform.petridish_pos = [66, 130]
        platform.petridish_radius = 45
        platform.pipette_1_pos = 0
        platform.pipette_2_pos = 0

        # Empty pipette
        # platform.dynamixel.write_profile_velocity(platform.settings["Tissues"]["Dropping speed"], ID=1)
        # platform.pipette_1_pos = 310
        # platform.dynamixel.write_pipette_ul(platform.pipette_1_pos, ID=1)
        # while not platform.dynamixel.pipette_is_in_position_ul(platform.pipette_1_pos, ID=1):
        #     continue

        # EMPTY PIPETTE SHOULD HAVE OWN BUTTON, GO TO CAMERA TOO

        # Putting on the more interesting camera feed
        # platform.camera_displayed_text.set("Camera 1")
        # platform.displayed_cameras = 1

        # if hasattr(platform, 'camera_feed_frame') and platform.camera_feed_frame.winfo_exists():
        #     platform.camera_feed_frame.destroy()
            
        platform.camera_feed_frame = tk.Frame(platform.tabControl.tab("Mode"))
        # Adjust the row and padding to lower the frame
        platform.camera_feed_frame.grid(row=1, column=1, padx=10, pady=20, rowspan=10)

        # Create a label to show the camera feed within the frame
        platform.camera_feed_label = tk.Label(platform.camera_feed_frame)
        platform.camera_feed_label.grid(row=0, column=0)

        if debug:
            platform.frame = cam_gear.get_cam_frame(platform.stream2)
        else:
            platform.frame = cam_gear.get_cam_frame(platform.stream1)
        # self.frame = self.cam.undistort(frame)
        imshow = platform.frame.copy()
        platform.show_frame(imshow)

        if platform.manual_mode:
            tm.sleep(3)

        print("-----------------------------------------------")
        print("The Target is at position : ", platform.target_pos)
        print("With offset, the target is : ", platform.target_pos[0] + platform.offset_check[0], platform.target_pos[1] + platform.offset_check[1])
        print("The current position is : ", platform.last_pos)
        print("-----------------------------------------------")
        print("Camera offset: ", platform.settings["Offset"]["Camera"])
        print("Tip offset: ", platform.settings["Offset"]["Tip one"])
        print("-----------------------------------------------")
        print("The Petridish is at position : ", platform.petridish_pos) 
        print("The Petridish radius is : ", platform.petridish_radius)
        print("The offset check is : ", platform.offset_check)

        # Check that this position is well inside the petridish 
        # Correction: Check that the position the tip will go to ...
        margin = 3 # with safety margins of 3
        # if (abs(platform.target_pos[0] + platform.offset_check[0] - platform.petridish_pos[0]) < platform.petridish_radius - margin and
        #     abs(platform.target_pos[1] + platform.offset_check[1] - platform.petridish_pos[1]) < platform.petridish_radius - margin and
        #     (platform.target_pos[0] + platform.offset_check[0] - platform.petridish_pos[0]) ** 2 + (platform.target_pos[1] + platform.offset_check[1] - platform.petridish_pos[1]) ** 2 < (platform.petridish_radius - margin) ** 2
        # ):
        #     print("!!!! Target position is outside of the petridish")
        #     platform.reset()

        #     tm.sleep(2)
        #     platform.camera_feed_label.destroy()
        #     platform.camera_feed_frame.destroy()
        #     return
        # else:
        #     print("!!!! Target position is inside of the petridish")

        # Let us put the offset check to 0 for now
        platform.offset_check = [0, 0]

        # Correction: Check that the position the tip will go to ...
        if (abs(platform.target_pos[0] + platform.offset_check[0] + platform.settings["Offset"]["Tip one"][0] - platform.settings["Offset"]["Camera"][0] - platform.petridish_pos[0]) > platform.petridish_radius - margin and
            abs(platform.target_pos[1] + platform.offset_check[1] + platform.settings["Offset"]["Tip one"][1] - platform.settings["Offset"]["Camera"][1] - platform.petridish_pos[1]) > platform.petridish_radius - margin and
            (platform.target_pos[0] + platform.offset_check[0] + platform.settings["Offset"]["Tip one"][0] - platform.settings["Offset"]["Camera"][0] - platform.petridish_pos[0]) ** 2 + (platform.target_pos[1] + platform.offset_check[1] + platform.settings["Offset"]["Tip one"][1] - platform.settings["Offset"]["Camera"][1] - platform.petridish_pos[1]) ** 2 > (platform.petridish_radius - margin) ** 2
        ):
            print("Check NR. 2 :  Target position is outside of the petridish")
            print("So what is up????????????")
            print("The target position is : ", platform.target_pos[0] + platform.offset_check[0], platform.target_pos[1] + platform.offset_check[1])
            print("The added offsets sum up to : ",platform.settings["Offset"]["Tip one"][0] - platform.settings["Offset"]["Camera"][0], platform.settings["Offset"]["Tip one"][1] - platform.settings["Offset"]["Camera"][1])   
            print("In total : ", platform.target_pos[0] + platform.offset_check[0] + platform.settings["Offset"]["Tip one"][0] - platform.settings["Offset"]["Camera"][0], platform.target_pos[1] + platform.offset_check[1] + platform.settings["Offset"]["Tip one"][1] - platform.settings["Offset"]["Camera"][1])   
            print("-----------------------------------------------")
            print("The petridish position is : ", platform.petridish_pos)
            print("The current position is : ", platform.last_pos)


            platform.reset()

            if platform.manual_mode:
                tm.sleep(2)
            platform.camera_feed_label.destroy()
            platform.camera_feed_frame.destroy()

            platform.tissue_picked = False

            return
        else:
            print("Check NR. 2 :  Target position is inside of the petridish")

        # Move to position
        # platform.move_xyz(
        #     x=platform.target_pos[0] + platform.offset_check[0] - platform.last_pos[0], 
        #     y=platform.target_pos[1] + platform.offset_check[1] - platform.last_pos[1], 
        #     z=platform.settings["Position"]["Pick height"] + platform.pick_offset - platform.last_pos[2])

        # With the two offsets added :
        platform.move_xyz(
            x=platform.target_pos[0] + platform.offset_check[0] + platform.settings["Offset"]["Tip one"][0] - platform.settings["Offset"]["Camera"][0] - platform.last_pos[0], 
            y=platform.target_pos[1] + platform.offset_check[1] + platform.settings["Offset"]["Tip one"][1] - platform.settings["Offset"]["Camera"][1] - platform.last_pos[1], 
            z=platform.settings["Position"]["Pick height"] + platform.pick_offset - platform.last_pos[2])

        # platform.move_xyz(
        #     x=platform.target_pos[0] + platform.offset_check[0] - platform.last_pos[0] - platform.settings["Offset"]["Camera"][0] + platform.settings["Offset"]["Tip one"][0], 
        #     y=platform.target_pos[1] + platform.offset_check[1] - platform.last_pos[1] - platform.settings["Offset"]["Camera"][1] + platform.settings["Offset"]["Tip one"][1], 
        #     z=platform.settings["Position"]["Pick height"] + platform.pick_offset - platform.last_pos[2])

        # For testing
        # platform.move_xyz(
        #     x=platform.target_pos[0] -19.5 - platform.last_pos[0],
        #     y=platform.target_pos[1] + 4.1 - platform.last_pos[1],
        #     z=platform.settings["Position"]["Pick height"] + platform.pick_offset - platform.last_pos[2])

        # ALL PICKING MOVEMENTS ARE WRONG, NEED TO BE ADJUSTED ?????????????????????????????????????????
       
        # platform.anycubic.move_axis_relative(
        #     x=platform.target_pos[0] + platform.offset_check[0], 
        #     y=platform.target_pos[1] + platform.offset_check[1], 
        #     z=platform.settings["Position"]["Pick height"] + platform.pick_offset, 
        #     f=platform.settings["Speed"]["Medium speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )

        if debug:
            platform.frame = cam_gear.get_cam_frame(platform.stream2)
        else:
            platform.frame = cam_gear.get_cam_frame(platform.stream1)
        imshow = platform.frame.copy()
        imshow = platform.cam.undistort(imshow)
        platform.show_frame(imshow)

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():

            # platform.show_frame(cam_gear.get_cam_frame(platform.stream1))
            if debug:
                platform.frame = cam_gear.get_cam_frame(platform.stream2)
            else:
                platform.frame = cam_gear.get_cam_frame(platform.stream1)

            success, platform.bbox = platform.tracker.update(platform.frame)

            if success:
                # Tracking success: Draw a rectangle around the tracked object
                print("Tracking success")
                # p1 = (int(platform.bbox[0]), int(platform.bbox[1]))
                # p2 = (int(platform.bbox[0] + platform.bbox[2]), int(platform.bbox[1] + platform.bbox[3]))

                # p1, p2 = platform.cam.platform_space_to_cam([p1, p2, platform.settings["Position"]["Pick height"]], platform.last_pos)

                # cv2.rectangle(platform.frame, p1, p2, (255,0,0), 2, 1)
                center = (int(platform.bbox[0]), int(platform.bbox[1]))
                imshow = cv2.drawMarker(imshow, center, (0, 255, 0), cv2.MARKER_SQUARE, 10, 2)
            else:
                # Tracking failure
                print("Tracking failure detected")
                #cv2.putText(platform.frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)

            # Display the frame with tracking information
            imshow = platform.frame.copy()
            imshow = platform.cam.undistort(imshow)
            platform.show_frame(imshow)

            print("Tracking the tissue while moving there")
            continue
    
        print("Moved to position")

        # tm.sleep(3)
        # platform.camera_feed_label.destroy()
        # platform.camera_feed_frame.destroy()
        # platform.update_idletasks()

        # return # for our testing purpose
    
        # Correction
        #platform.delay(0.3)
        x, y, w, h = platform.bbox
        target_px = [int(x + w / 2), int(y + h / 2)]
        cam_pos = (
            platform.target_pos[0] + platform.offset_check[0] - platform.settings["Offset"]["Camera"][0] + platform.settings["Offset"]["Tip one"][0],
            platform.target_pos[1] + platform.offset_check[1] - platform.settings["Offset"]["Camera"][1] + platform.settings["Offset"]["Tip one"][1],
            platform.settings["Position"]["Pick height"] + platform.pick_offset - platform.settings["Offset"]["Camera"][2] + platform.settings["Offset"]["Tip one"][2]
        )
        #platform.target_pos = platform.cam.cam_to_platform_space(target_px, cam_pos)
        if (platform.target_pos[0] - platform.petridish_pos[0]) ** 2 + (platform.target_pos[1] - platform.petridish_pos[1]) ** 2 > platform.petridish_radius ** 2:
            print("Check NR. 3 : Target position is outside of the petridish")
            platform.reset()
            platform.tissue_picked = False

            if platform.manual_mode:
                tm.sleep(2)
            platform.camera_feed_label.destroy()
            platform.camera_feed_frame.destroy()
            return
        else:
            print("Check NR. 3 : Target position is inside of the petridish")

        if debug:
            platform.frame = cam_gear.get_cam_frame(platform.stream2)
        else:
            platform.frame = cam_gear.get_cam_frame(platform.stream1)
        imshow = platform.frame.copy()
        center = (int(target_px[0]), int(target_px[1]))
        # Draw a circle using cv2.drawMarker around the detected tissue
        imshow = cv2.drawMarker(imshow, center, (0, 255, 0), cv2.MARKER_SQUARE, 10, 2)    
        platform.show_frame(imshow) 

        # man_corr = [0., 1.0]
        # platform.anycubic.move_axis_relative(
        #     x=platform.target_pos[0] + man_corr[0], 
        #     y=platform.target_pos[1] + man_corr[1], 
        #     z=platform.settings["Position"]["Pick height"], 
        #     f=platform.settings["Speed"]["Slow speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        # What is this man correction??

        # platform.anycubic.finish_request()
        # while not platform.anycubic.get_finish_flag():
        #     continue

        # Suck
        platform.pipette_1_pos -= platform.settings["Tissues"]["Pumping Volume"]
        platform.dynamixel.write_profile_velocity(platform.settings["Tissues"]["Pumping speed"], ID=1)
        platform.dynamixel.write_pipette_ul(platform.pipette_1_pos, ID=1)
        # while not platform.dynamixel.pipette_is_in_position_ul(platform.pipette_1_pos, ID=1):
        #     continue
        # while platform.dynamixel.read_position(ID = 1) > platform.pipette_1_pos:
        #     print("Sucking up the tissue; we are at: ", platform.dynamixel.read_position(ID = 1), " instead of ", platform.pipette_1_pos)   
        #     continue

        print("Sucked up the tissue")

        # Check pickup
        # platform.anycubic.move_axis_relative(
        #     z=platform.settings["Position"]["Pick height"] + platform.pick_offset, 
        #     f=platform.settings["Speed"]["Slow speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        # platform.anycubic.move_axis_relative(
        #     x=platform.target_pos[0] + platform.offset_check[0], 
        #     y=platform.target_pos[1] + platform.offset_check[1], 
        #     f=platform.settings["Speed"]["Slow speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )


        # What is this ????????
        #platform.move_xyz(x=platform.target_pos[0] + platform.offset_check[0], y=platform.target_pos[1] + platform.offset_check[1], z=platform.settings["Position"]["Pick height"] + platform.pick_offset)

        # Instead this? :
        platform.move_xyz(z=platform.settings["Position"]["Pick height"] + platform.pick_offset + 10 - platform.last_pos[2])  

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue
        print("Moved up a bit")

        if platform.check_pickup():
            platform.release_tracker()

            #platform.take_picture()
            # function needs to be adapted still

            platform.tissue_picked = True
            print("Pickup successful after attempt " + str(platform.pick_attempt))
            platform.pick_attempt = 0
            platform.message_box.delete('1.0', tk.END)
            platform.update_idletasks()
        else:
            platform.pick_attempt += 1
            platform.tissue_picked = False

            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "Pickup failed after attempt " + str(platform.pick_attempt))
            platform.message_box.see(tk.END)
            platform.update_idletasks()
            logger.info("Pickup failed after attempt " + str(platform.pick_attempt))

            # platform.pick()

        # wait 2s before destroying camera feed
        if platform.manual_mode:
            tm.sleep(2)

        platform.camera_feed_label.destroy()
        platform.camera_feed_frame.destroy()

    def place(platform):

        if platform.is_homed == False:

            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            platform.message_box.see(tk.END)
            platform.update_idletasks()

            logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            return
        
        print("Place function started!")
        # Move to position
        dest = platform.destination()
       
       # Move to safe height
        # platform.anycubic.move_axis_relative(
        #     z=platform.safe_height, 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        platform.move_xyz(z=platform.safe_height) 

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue

        # if dest[1] > 100:
        #     platform.anycubic.move_axis_relative(
        #         x=80, 
        #         y=100, 
        #         f=platform.settings["Speed"]["Fast speed"], 
        #         offset=platform.settings["Offset"]["Tip one"]
        #     )
        # platform.anycubic.move_axis_relative(
        #     x=dest[0], 
        #     y=dest[1], 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )

        platform.message_box.delete('1.0', tk.END)
        platform.message_box.insert(tk.END, "Now going to well number " + str(platform.well_num))
        platform.message_box.see(tk.END)
        platform.update_idletasks()

        print("Now going to well number ", platform.well_num)
        print("We have to move ", dest[0] - platform.last_pos[0], dest[1] - platform.last_pos[1])
        platform.move_xyz(x=dest[0] - platform.last_pos[0], y=dest[1] - platform.last_pos[1])

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            # print("Waiting for the printer to finish moving there")
            continue    
        
        # Go down
        print("Going down to drop height")

        platform.message_box.delete('1.0', tk.END)
        platform.message_box.insert(tk.END, "Going down to drop height")
        platform.message_box.see(tk.END)
        platform.update_idletasks()

        # platform.anycubic.move_axis_relative(
        #     z=platform.settings["Position"]["Drop height"], 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        platform.move_xyz(z=platform.settings["Position"]["Drop height"] - platform.last_pos[2])

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue 

        # Blow
        print("Blowing")

        platform.message_box.delete('1.0', tk.END)
        platform.message_box.insert(tk.END, "Blowing")
        platform.message_box.see(tk.END)
        platform.update_idletasks()

        platform.dynamixel.write_profile_velocity(platform.settings["Tissues"]["Dropping speed"], ID=1)
        print(1)
        platform.pipette_1_pos = platform.pipette_1_pos + platform.settings["Tissues"]["Dropping volume"]
        if debug:
            platform.dynamixel.write_pipette(platform.pipette_1_pos / (PIPETTE_MAX[0]-PIPETTE_MIN[0]), ID=1)
            print(2)
            while not platform.dynamixel.pipette_is_in_position(platform.pipette_1_pos / (PIPETTE_MAX[0]-PIPETTE_MIN[0]), ID=1):
                continue
        #elif platform.pipette_1_pos < PIPETTE_MIN[0]:
        elif platform.pipette_1_pos >= 570:
            print("There is not enough liquid in the pipette to drop anything")

            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "There is not enough liquid in the pipette!")
            platform.message_box.see(tk.END)
            platform.update_idletasks()
        else:
            platform.dynamixel.write_pipette_ul(platform.pipette_1_pos, ID=1)
            print(3)
            while not platform.dynamixel.pipette_is_in_position_ul(platform.pipette_1_pos, ID=1):
                continue

        # Go up
        print("Going up")

        platform.message_box.delete('1.0', tk.END)
        platform.message_box.insert(tk.END, "Going up!")
        platform.message_box.see(tk.END)
        platform.update_idletasks()

        # platform.anycubic.move_axis_relative(
        #     z=platform.safe_height, 
        #     f=platform.settings["Speed"]["Fast speed"], 
        #     offset=platform.settings["Offset"]["Tip one"]
        # )
        platform.move_xyz(z=platform.safe_height)

        platform.anycubic.finish_request()
        while not platform.anycubic.get_finish_flag():
            continue

        # Post placement actions (reset sample count or move to next well)
        print("Post placement actions")
        platform.nb_sample += 1
        if platform.nb_sample >= platform.settings["Well"]["Number of sample per well"]:
            platform.well_num += 1
            platform.nb_sample = 0
            #if platform.well_num >= len(platform.culture_well):
            if platform.well_num >= platform.settings["Well"]["Number of well"]:
                logger.info("All wells are completed.")

                platform.message_box.delete('1.0', tk.END)
                platform.message_box.insert(tk.END, "All wells are completed.")
                platform.message_box.see(tk.END)
                platform.update_idletasks()

                #platform.reset()
            else:
                logger.info("Moving to next well.")

                platform.message_box.delete('1.0', tk.END)
                platform.message_box.insert(tk.END, "Moving to next well.")
                platform.message_box.see(tk.END)
                platform.update_idletasks()

                platform.reset()
        else:
            logger.info("Ready for next sample.")

            platform.message_box.delete('1.0', tk.END)
            platform.message_box.insert(tk.END, "Ready for next sample.")
            platform.message_box.see(tk.END)
            platform.update_idletasks()

            platform.reset() 
        print("Place function ended!") 

        # Wait 2s
        if platform.manual_mode:
            tm.sleep(2)

        platform.message_box.delete('1.0', tk.END)
        platform.update_idletasks()  

    def pick_and_place(self):

        if self.is_homed == False:
            logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.tip_calibration_done == False:
            logger.info("Tip calibration not done yet, please do a calibration first!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        self.manual_mode = False

        self.tissue_detected = False
        while not self.tissue_detected or self.target_pos is None:
            self.detect()

        self.tissue_picked = False
        while not self.tissue_picked:
            self.pick()

        if self.take_picture():
            self.place()
        else:
            self.reset()

        self.manual_mode = True

        logger.info("Pick and Place complete!")
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Pick and Place complete!")
        self.message_box.see(tk.END)
        self.update_idletasks()

    def run_all(self):

        if self.is_homed == False:
            logger.info("Printer not even homed yet, please home the printer first! Full calibration recommended!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Printer not even homed yet! Full calibration recommended!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        if self.tip_calibration_done == False:
            logger.info("Tip calibration not done yet, please do a calibration first!")
            
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Tip calibration not done yet, please do a calibration first!")
            self.message_box.see(tk.END)
            self.update_idletasks()
            return
        
        self.manual_mode = False

        while self.well_num < self.settings["Well"]["Number of well"]:
            self.pick_and_place()

            logger.info("Number of samples placed: " + str(self.well_num * self.settings["Well"]["Number of sample per well"] + self.nb_sample))
            self.message_box.delete('1.0', tk.END)
            self.message_box.insert(tk.END, "Number of samples placed: " + str(self.well_num * self.settings["Well"]["Number of sample per well"] + self.nb_sample))
            self.message_box.see(tk.END)
            self.update_idletasks()
        
        self.manual_mode = True

        logger.info("Run all is completed! Total number of samples placed: " + str(self.well_num * self.settings["Well"]["Number of sample per well"] + self.nb_sample))    
        self.message_box.delete('1.0', tk.END)
        self.message_box.insert(tk.END, "Run all is completed! Total number of samples placed: " + str(self.well_num * self.settings["Well"]["Number of sample per well"] + self.nb_sample))
        self.message_box.see(tk.END)
        self.update_idletasks()


    def first_function(self):
        print("This is the start of the testing function guys!!")
        
        # self.move_home()
        # self.detect()

        # self.offsetcalibration()
        # self.tip_calibration_done = True

        # print("This is the end of the testing function guys!!")

if __name__ == "__main__":
    window = MyWindow()
    
    window.add_function_to_buffer(window.first_function())

    ## Equivalent to window.mainloop()
    while window.isOpen:
        window.update_cameras()
        window.execute_function_from_buffer()   
        window.update()
        window.update_idletasks()
        


        