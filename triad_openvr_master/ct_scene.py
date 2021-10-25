"""Example showing a volume rendered CT scan and a polygonal liver"""

import os
import vtk
import sys
import time

# Set up paths to data files
curdir = os.path.dirname(__file__)
CT_FILE = os.path.join(curdir, '../data/volume-105.nhdr')
LIVER_FILE = os.path.join(curdir, '../data/Liver.stl')

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
renderer.AddVolume(volume)

# Load the polygonal (e.g., surface) data of the liver. This is stored
# as an STL.
reader = vtk.vtkSTLReader()
reader.SetFileName(LIVER_FILE)

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(reader.GetOutputPort())
mapper.SetScalarVisibility(0)

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetColor([0.2, 1.0, 0.2])
actor.GetProperty().SetOpacity(1.0)
actor.GetProperty().SetInterpolationToPhong()
actor.GetProperty().SetRepresentationToSurface()
renderer.AddActor(actor)

renderer.ResetCamera()
renderer.ResetCameraClippingRange()
window_interactor.Start()
