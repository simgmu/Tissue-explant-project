# Tissue explant project

## Objectives
In the context of tumor research, personalized medical treatments are very expensive and not widely accessible. One aspect of the research involves isolating samples from a biopsy to test several treatments on the same tumor. This project aims to develop a robotic platform capable of selecting, moving, and culturing these different samples to streamline the resulting research and make the technique more affordable.

## Hardware


The project use the frame from a 3D printer, an anycubic mega zero with it's controller. A webcam is used in order to detect and track the samples and three dynamixel xl430 are used to actuate two micro-pipette in order to act like a pneumatic gripper and to automate the manipulation of liquids.

One of the tips is used exclusively for moving the samples while the second one is used to mix and place the gel matrix with the nutriments in order to keep the samples alive. Both tips are selectable using an actuator and are connected to individual micropipettes, ensuring a precision of ±3uL while allowing simultaneous use of both tips.


## Computer vision
One of the main constraint of this project was to be able to detect and select the tissue samples. The webcam placed at the end effector of the robot makes it possible. The camera gives the position of the particles and it is also used to check if the samples are correctly picked up by the tip of the pipette. 

The first challenge was to guarantee a high precision, under the milimeter scale for the evaluation of the position of the particles. 
The second aspect is to detect and select the different samples taking into account their size and shape to ensure more representative results.

In order to increase the reliability of the platform a second camera is used to validate the catch. A macro camera is used on the side to evaluate the tip.

## Results

The platform as been tested on diffrent types of samples. The differents results as been collected on mouse samples, spleen, kidney and colon tissues. 
Depending on the selected settings, it was possible to perform pick and place in only about 22s and adding two macro camera checks and a tip emtying, in about 47s. Gel preparation and application was possible (depending on the selected settings) in about 1min20s. Those duration measurements are consistent between runs with manual assistance and completely autonomous runs.