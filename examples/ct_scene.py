"""Example showing a volume rendered CT scan and a polygonal liver"""


import triad_openvr
import os
import vtk
import time
from vtkmodules.vtkFiltersSources import vtkSphereSource

# Set up paths to data files
curdir = os.path.dirname(__file__)
CT_FILE = os.path.join(curdir, '../data/volume-105.nhdr')
NEEDLE_FILE = os.path.join(curdir, '../data/handler.stl')

REFRESH_RATE = 60

connecting = False
v = triad_openvr.triad_openvr()
# position = v.devices["controller_1"].get_pose_euler()
# position[x, y, z, yaw, pitch, roll]

while(True):
    position = v.devices["controller_1"].get_pose_euler()

    start = time.time()
    message = ""
    if not hasattr(position, '__iter__'):
        message = "Waiting for controller."
        print("\r" + message, end="")
        sleep_time = 1/REFRESH_RATE-(time.time()-start)
        if sleep_time > 0:
            time.sleep(sleep_time)
    else:
        print("\r" + "Start to initial VTK window.", end="")
        connecting = True
        break


# Initialize renderer, window, and the specific interaction (e.g., mouse mapping) style
renderer = vtk.vtkRenderer()

render_window = vtk.vtkRenderWindow()
render_window.SetSize(600, 600)
render_window.AddRenderer(renderer)

interaction_style = vtk.vtkInteractorStyleTrackballCamera()
window_interactor = vtk.vtkRenderWindowInteractor()
window_interactor.SetRenderWindow(render_window)
window_interactor.SetInteractorStyle(interaction_style)
window_interactor.Initialize()


def callback_func(caller, timer_event):
    # fetch the position data
    position = v.devices["controller_1"].get_pose_euler()
    # fetch the controller button data
    controller_status = v.devices["controller_1"].get_controller_inputs()
    txt = ""
    if not hasattr(position, '__iter__'):
        connecting = False
        needle_actor.GetProperty().SetColor([1, 1, 1])
        print("\r" + "Waiting", end="")
    else:
        connecting = True
        for each in position:
            txt += "%.4f" % each
            txt += " "
        print("\r" + txt, end="")

        # since the pressure on the trigger is from 0 to 1,
        # I decided compute the trigger strength use 1 - controller_status['trigger']
        # change the color of the needle from (1, 1, 1) to (1, 1 * trigger strength, )
        if(controller_status['trigger'] > 0.1):
            print(controller_status)
            trigger_strength = 1-controller_status['trigger']
            needle_actor.GetProperty().SetColor(
                [1, 1*trigger_strength, 1*trigger_strength])
        else:
            # when release the trigger, change the color of needle to white.
            needle_actor.GetProperty().SetColor([1, 1, 1])

        # Reset the needle position and orientation based on the 6dof data
        needle_actor.SetPosition(position[0] * -700, position[1]
                                 * 700 - 300, position[2]*-700)
        needle_actor.SetOrientation(-position[5], -position[4], -position[3])

    # check if the controller is within the basestation view
    if(connecting):
        sphere_actor.GetProperty().SetColor([0, 1, 0])
    else:
        sphere_actor.GetProperty().SetColor([1, 0, 0])
    render_window.Render()


window_interactor.CreateRepeatingTimer(int(1/REFRESH_RATE))
window_interactor.AddObserver("TimerEvent", callback_func)


# Load the CT scan


reader = vtk.vtkNrrdReader()
reader.SetFileName(CT_FILE)
reader.Update()

print('CT Origin: ',       reader.GetOutput().GetOrigin())
print('CT Spacing: ',      reader.GetOutput().GetSpacing())
print('CT Extent: ',       reader.GetOutput().GetExtent())
print('CT Scalar range: ', reader.GetOutput().GetScalarRange())

# Volume render the CT scan, using a mapping from CT scan intensities
# to color and opacity that will highlight bones
color_transfer_function = vtk.vtkColorTransferFunction()
color_transfer_function.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
color_transfer_function.AddRGBPoint(-16, 0.73, 0.25, 0.30, 0.49, .61)
color_transfer_function.AddRGBPoint(641, .90, .82, .56, .5, 0.0)
color_transfer_function.AddRGBPoint(3070, 1.0, 1.0, 1.0, .5, 0.0)
color_transfer_function.AddRGBPoint(3071, 0.0, .333, 1.0, .5, 0.0)

opacity_transfer_function = vtk.vtkPiecewiseFunction()
opacity_transfer_function.AddPoint(-3024, 0, 0.5, 0.0)
opacity_transfer_function.AddPoint(-16, 0, .49, .61)
opacity_transfer_function.AddPoint(641, .72, .5, 0.0)
opacity_transfer_function.AddPoint(3071, .71, 0.5, 0.0)

volume_mapper = vtk.vtkGPUVolumeRayCastMapper()
volume_mapper.SetInputConnection(reader.GetOutputPort())

volume_property = vtk.vtkVolumeProperty()
volume_property.SetColor(color_transfer_function)
volume_property.SetScalarOpacity(opacity_transfer_function)
volume_property.SetInterpolationTypeToLinear()
volume_property.ShadeOn()
volume_property.SetAmbient(0.1)
volume_property.SetDiffuse(0.9)
volume_property.SetSpecular(0.2)
volume_property.SetSpecularPower(10.0)
volume_property.SetScalarOpacityUnitDistance(0.8919)


volume = vtk.vtkVolume()
volume.SetMapper(volume_mapper)
volume.SetProperty(volume_property)
volume.RotateX(-90)
renderer.AddVolume(volume)

# Load the polygonal (e.g., surface) data of the liver. This is stored
# as an STL.


# ==========================Arrow=====================================
# arrowSource = vtk.vtkArrowSource()

# mapper = vtk.vtkPolyDataMapper()
# mapper.SetInputConnection(arrowSource.GetOutputPort())
# mapper.SetScalarVisibility(0)
# actor = vtk.vtkActor()
# actor.SetMapper(mapper)

# ===============================================================
# create connecting indicator using a sephere
sphere_source = vtkSphereSource()
sphere_source.SetCenter(0.0, 0.0, 0.0)
sphere_source.SetRadius(20.0)
sphere_source.SetPhiResolution(100)
sphere_source.SetThetaResolution(100)
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(sphere_source.GetOutputPort())
sphere_actor = vtk.vtkActor()
sphere_actor.SetMapper(mapper)
sphere_actor.GetProperty().SetColor([0, 1, 0])
renderer.AddActor(sphere_actor)

# ========================STL=======================================
reader = vtk.vtkSTLReader()
reader.SetFileName(NEEDLE_FILE)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(reader.GetOutputPort())
mapper.SetScalarVisibility(0)

needle_actor = vtk.vtkActor()
needle_actor.SetMapper(mapper)

# ===============================================================

needle_actor.SetPosition(0, 0, 0)
needle_actor.GetProperty().SetColor([1, 1, 1])
needle_actor.GetProperty().SetOpacity(1)
needle_actor.GetProperty().SetInterpolationToPhong()
needle_actor.GetProperty().SetRepresentationToSurface()
renderer.AddActor(needle_actor)

renderer.ResetCamera()
renderer.ResetCameraClippingRange()
window_interactor.Start()
