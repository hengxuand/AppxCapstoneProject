import sys
import vtk
from PyQt5 import QtCore, QtGui
from PyQt5 import Qt
import os

from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor


# def get_program_parameters():
#     import argparse
#     description = 'Read a .stl file.'
#     epilogue = ''''''
#     parser = argparse.ArgumentParser(description=description, epilog=epilogue,
#                                      formatter_class=argparse.RawDescriptionHelpFormatter)
#     parser.add_argument('filename', help='42400-IDGH.stl')
#     args = parser.parse_args()
#     return args.filename


class RenderWindow(Qt.QMainWindow):

    def __init__(self, ct_file, stl_file, parent=None, ):
        Qt.QMainWindow.__init__(self, parent)
        self.setWindowTitle("VTK Render Window")

        print("VTK Render Window Start")
        # setup Qt frame
        self.frame = Qt.QFrame()
        # self.frame.setMinimumSize(1024,600)
        self.vl = Qt.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)

        print("setup vtk render")
        # setup vtk render
        self.ren = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()
        # self.vtkWidget.UpdateSize(1024, 600)

        print("read file")
        # # read file
        curdir = os.path.dirname(__file__)
        CT_FILE = os.path.join(curdir, ct_file)
        LIVER_FILE = os.path.join(curdir, stl_file)

        # # read CT file
        print(ct_file)
        nrrdreader = vtk.vtkNrrdReader()

        nrrdreader.SetFileName(CT_FILE)
        nrrdreader.Update()

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

        volMapper = vtk.vtkGPUVolumeRayCastMapper()
        volMapper.SetInputConnection(nrrdreader.GetOutputPort())

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
        volume.SetMapper(volMapper)
        volume.SetProperty(volume_property)
        self.ren.AddVolume(volume)

        # read STL file
        stlReader = vtk.vtkSTLReader()
        print(stl_file)
        stlReader.SetFileName(LIVER_FILE)

        stlMapper = vtk.vtkPolyDataMapper()
        stlMapper.SetInputConnection(stlReader.GetOutputPort())

        # Create an actor
        actor = vtk.vtkActor()
        actor.SetMapper(stlMapper)

        self.ren.AddActor(actor)

        self.ren.ResetCamera()

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.show()
        self.iren.Initialize()
        self.iren.Start()

