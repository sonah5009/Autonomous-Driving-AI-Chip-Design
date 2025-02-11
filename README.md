# AutoLab_SoC Driving Project File Structure

2025 Winter Extracurricular Program: Autonomous Driving SoC Design for Students

---

## Folder Structure

### debugging
- **SoC_Driving.ipynb**  
  *Jupyter Notebook for driving code*
- **data_collection.ipynb**  
  *Jupyter Notebook for data collection*

### dpu
- **dpu.bit**  
  *DPU bitstream file **(Students need to add)***
- **dpu.hwh**  
  *DPU hardware file **(Students need to add)***
- **dpu.xclbin**  
  *DPU executable file **(Students need to add)***

### driving
- **config.py**  
  *Initial motor address settings*
- **driving_system_controller.py**  
  *Driving mode settings*
- **image_processor.py**  
  *Image processing script*
- **main.py**  
  *Driving parameter settings*
- **motor_controller.py**  
  *Motor control settings*
- **yolo_utils.py**  
  *YOLO utility functions*

### test_video
- **test_video.mp4**  
  *Test video file*

### xmodel
- **lane_class.txt**  
  *Model class configuration **(Students need to add)***
- **top-tiny-yolov3_coco_256.xmodel**  
  *Compiled deep learning model file **(Students need to add)***

---


# AutoLab SoC Driving - Student Modification Guide

This section outlines the key parts of each file that students need to modify. Review the details and file locations carefully before making changes.

---

## 1. main.py

Here are the lines of code you need to update:

```python
# Line 36
speed = 0

# Line 37
steering_speed = 50

# Line 47
overlay = DpuOverlay("./dpu/dpu.bit")

# Line 48
overlay.load_model("./xmodel/top-tiny-yolov3_coco_256.xmodel")
```

---

## 2. config.py

Modify the following parts of the file:

```python
# Line 9
MOTOR_ADDRESSES = {
    'motor_0': 0x00A0000000,
    'motor_1': 0x00A0010000,
    'motor_2': 0x00A0020000,
    'motor_3': 0x00A0030000,
    'motor_4': 0x00A0040000,
    'motor_5': 0x00A0050000
}

# Line 18
ADDRESS_RANGE = 0x10000

# Line 23
classes_path = "./xmodel/lane_class.txt"
```

---

## 3. motor_controller.py

You need to update lines 53-54 and make changes to specific functions:

```python
# Lines 53-54
register_most_left, register_most_right
```

### Functions to modify:
- **def right()**  
- **def left()**  
- **def stay()**  
- **def set_left_speed()**  
- **def set_right_speed()**

### Motor Control Algorithm:
- **def control_motors()**

---

## 4. image_processor.py

Update the following variables in the file:

```python
# Variable settings
self.reference_point_x = 190
self.reference_point_y = 150
self.point_detection_height = 20
right_lane_angle = 90
```

---

## Notes

- Double-check file names and line numbers before making changes.  
- Save all changes and test the project to confirm everything works correctly.
