# AppxCapstoneProject

## Runtime Setup:

On Windows, following [this](https://katiekodes.com/setup-python-windows-miniconda/):

- Download the [Python 3.9 miniconda, 64 bit](https://repo.anaconda.com/miniconda/Miniconda3-py39_4.9.2-Windows-x86_64.exe):
- Run it
- Install for All Users
- Change the installation folder to C:\Miniconda3
- Leave the advanced options as the default
  - Don't add Miniconda to system path
  - Do register Miniconda as system python 3.9
- This causes your python.exe to be at Miniconda3\python.exe
- Now, to run any python programs, start with the "Anaconda Prompt",
  which is in your start folder. This will manage your active virtual
  environment for you.
- Note that virtual enviroments will be stored in C:\Miniconda3\envs
- Add c:\Miniconda3\condabin to your path (individual user) so that
  the conda command is available everywhere. See
  [here](https://helpdeskgeek.com/windows-10/add-windows-path-environment-variable/)
  for instructions on how to add to the path.

## Update conda

Even after you run these, you may not have the latest and greatest. In
the conda shell, run:

    conda update -n base -c defaults conda

Accept everything. Ignore the warnings about manually removing old
versions.

Close this prompt window, and start a new one.

## Conda environment

Set up our shared conda environment for vtk development, which will be named
"csvtk". In the conda-integrated prompt or shell, from the directory
where the environment.yml file is located, run:

    conda env create --file=environment.yml

This will create a new enviroment named "csvtk", with all of the
dependencies installed. To activate this enviroment in a command line,
run:

    conda activate csvtk

To install openvr, run: 
    
    pip install openvr

## Download the STL files

Download all the files from [Google](https://drive.google.com/drive/folders/1L5b4ZtSEj2PbfLwiy2nHqTtkQs8hzTMZ?usp=sharing) and store them in the data folder in this project.


## External softwares:

 - Download Steam and SteamVR. 
    - In the SteamVR page, on the right side, click the gear button and click Properties... ![Screenshot](data\steamvr-page.png)

    
    - On the pop-up window, click BETAS, choose beta - SteamVR Beta Update.![Screenshot](data\SteamVR-BETAS.png)
 - SteamVR NULL driver configuration.
    - open the file "Steam\config\steamvr.vrsettings"
    - In the value of key steamvr, add: 
        
        "activateMultipleDrivers" : true,  
        "forcedDriver": "null",
    - After the steamvr object, add:  
      "driver_null" : {  
           "enable" : true,  
           "serialNumber" : "Null Serial Number",   
           "modelNumber" : "Null Model Number",  
           "windowX" : 0,  
          "windowY" : 0,  
          "windowWidth" : 1920,  
          "windowHeight" : 1080,  
          "renderWidth" : 1920,  
          "renderHeight" : 1060,  
          "secondsFromVsyncToPhotons" : 0.01111111,  
          "displayFrequency" : 60.0  
      }
## VR Device Setup Tips:

- Plug the base station with the power on the wall.
- Base Station: Place it facing a open space in all angles. Choose the edge instead of the center of a table.
- Connect the controller with computer using USB cable in the box.
- Controller: Move the controller in a distance from 30cm - 2m to ensure the base station can capture the signals from the controller.

## Run the application

    python app.py

# Features

- Keyboard:
  - "W": Toggle the liver between wireframe version and surface version.
  - "S": Toggle the skeleton visibility.
  - "L": Toggle the liver visibility.
  - "T": Toggle the tumor visibility.
  - "F1": Hold and toggle the first 2D slice view
  - "F2": Hold and toggle the second 2D slice view
  - "F3": Hold and toggle the thrid 2D slice view
  - "F4": Toggle the 2-D-slice views' simultaneously update along the needle.
- Controller:
  - Trigger - Ultra-sound processing.
  - Trackpad pressing - Rotation of the camera.
  - Trackpad touching with grip button holding - Zooming.
