import triad_openvr
import vtk
import time
from PyQt5 import Qt
from PyQt5 import QtGui
from PyQt5 import QtCore
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonColor import vtkNamedColors
from datetime import date
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkImageActor)


class RenderWindow(Qt.QMainWindow):

    def __init__(self, ct_file, stl_file, parent=None, ):
        Qt.QMainWindow.__init__(self, parent)
        self.setWindowTitle("VTK Render Window")

        self.REFRESH_RATE = 60
        self.volume_visible = True
        self.volume_pressed = False
        # setup vive controller & check the if controller is in the range
        self.vivecontrol = triad_openvr.triad_openvr()
        self.zoom_var = 0.0
        self.liver_hp = 100

        # logo
        self.setWindowIcon(QtGui.QIcon('./data/logo.png'))

        print("VTK Render Window Start")
        # setup Qt frame
        self.frame = Qt.QFrame()
        self.frame.setStyleSheet("background-color: black")
        self.vl = Qt.QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)

        print("setup vtk render")
        # setup vtk render
        self.rw = self.vtkWidget.GetRenderWindow()
        self.iren = self.rw.GetInteractor()

        # setup trackballcamera
        interaction_style = vtk.vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(interaction_style)
        self.iren.Initialize()

        # register callback
        self.iren.CreateRepeatingTimer(int(1 / self.REFRESH_RATE))
        self.iren.AddObserver("TimerEvent", self.callback_func)
        self.iren.SetRenderWindow(self.rw)

        # get sources
        sources = self.get_sources(ct_file, stl_file)
        # create liver actor to be added later on
        stlMapper = vtk.vtkPolyDataMapper()
        stlMapper.SetInputConnection(sources[1].GetOutputPort())
        stlMapper.SetScalarVisibility(0)
        self.liver_actor = vtk.vtkActor()
        self.liver_actor.SetMapper(stlMapper)
        self.liver_actor.RotateX(-90)
        self.liver_actor.GetProperty().SetColor(1, 1, 1)
        self.liver_actor.GetProperty().SetOpacity(0.6)

        # render main screen
        print("render main screen")
        self.main_ren = self.vtkRender(0)
        self.rw.AddRenderer(self.main_ren)
        self.camera = self.main_ren.GetActiveCamera()

        volMapper = vtk.vtkGPUVolumeRayCastMapper()
        volMapper.SetInputConnection(sources[0].GetOutputPort())

        self.volume = vtk.vtkVolume()
        self.volume.SetMapper(volMapper)
        self.volume.SetProperty(self.vtkVolume())
        self.volume.RotateX(-90)

        # read needle and tumor
        # load needle and create actor
        needle_reader = vtk.vtkSTLReader()
        needle_reader.SetFileName("./data/needle.stl")
        needle_mapper = vtk.vtkPolyDataMapper()
        needle_mapper.SetInputConnection(needle_reader.GetOutputPort())
        needle_mapper.SetScalarVisibility(0)
        self.needle_actor = vtk.vtkActor()
        self.needle_actor.SetMapper(needle_mapper)
        self.needle_actor.SetScale(5)
        self.needle_actor.GetProperty().SetColor([1, 1, 1])
        self.needle_actor.GetProperty().SetOpacity(1)
        self.needle_actor.GetProperty().SetInterpolationToPhong()
        self.needle_actor.GetProperty().SetRepresentationToSurface()

        # load tumor
        tumor_reader = vtk.vtkSTLReader()
        tumor_reader.SetFileName("./data/mass.stl")
        tumor_mapper = vtk.vtkPolyDataMapper()
        tumor_mapper.SetInputConnection(tumor_reader.GetOutputPort())
        tumor_mapper.SetScalarVisibility(0)
        self.tumor_actor = vtk.vtkActor()
        self.tumor_actor.SetMapper(tumor_mapper)
        self.tumor_actor.SetPosition(0, 0, 0)
        self.tumor_actor.SetPosition([-200, -390, 200])
        self.tumor_actor.GetProperty().SetColor([1, 0.6, 0.2])
        self.tumor_actor.GetProperty().SetOpacity(1)
        # self.tumor_actor.GetProperty().SetInterpolationToPhong()
        self.tumor_actor.GetProperty().SetRepresentationToSurface()

        # actors collision detection
        # self.matrix1 = vtk.vtkMatrix4x4()
        # self.transform0 = vtk.vtkTransform()
        # self.collide = vtk.vtkCollisionDetectionFilter()
        # self.collide.SetInputConnection(0, sources[1].GetOutputPort())
        # self.collide.SetTransform(0, self.transform0)
        # self.collide.SetInputConnection(1, needle_reader.GetOutputPort())
        # self.collide.SetMatrix(1, self.matrix1)
        # self.collide.SetBoxTolerance(0.0)
        # self.collide.SetCellTolerance(0.0)
        # self.collide.SetNumberOfCellsPerNode(2)
        # self.collide.SetCollisionModeToAllContacts()
        # self.collide.GenerateScalarsOn()
        # print("self.collide.GetNumberOfContacts()")

        self.main_ren.AddVolume(self.volume)
        self.main_ren.AddActor(self.needle_actor)
        self.main_ren.AddActor(self.liver_actor)
        self.main_ren.AddActor(self.tumor_actor)

        # logo
        reader = vtk.vtkPNGReader()
        reader.SetFileName("./data/logo.png")
        reader.Update()
        logo = vtk.vtkLogoRepresentation()
        logo.SetImage(reader.GetOutput())

        # logo.ProportionalResizeOn()
        # logo.SetPosition(20, 20)
        # logo.SetPosition2(10,10)
        # logoWidget = vtk.vtkLogoWidget()

        # imageActor.SetInputData(reader.GetOutput())
        #main_ren.SetViewport(xmins[0], ymins[0], xmaxs[0], ymaxs[0])

        self.main_ren.AddActor(self.txtActor(
            2, 42, 15, 'Patient name: Alex Smith'))
        self.main_ren.AddActor(self.txtActor(2, 22, 15, 'Age: 40 - F'))
        todaystr = date.today().strftime("%m-%d-%Y")
        self.main_ren.AddActor(self.txtActor(2, 2, 15, todaystr))
        self.main_ren.AddActor(self.txtActor(
            1, 1, 15, 'Patient name: Hengxuan'))

        # render side window
        print("render side screen 1")
        side_ren1 = self.vtkRender(1)
        side_ren1.AddViewProp(logo)
        logo.SetRenderer(side_ren1)
        self.rw.AddRenderer(side_ren1)
        # side_ren1.SetViewport(xmins[1], ymins[1], xmaxs[1], ymaxs[1])
        side_ren1.SetActiveCamera(self.camera)
        side_ren1.AddActor(self.liver_actor)

        side_ren1.ResetCamera()
        side_ren1.ResetCameraClippingRange()

        side_ren2 = self.vtkRender(2)
        (sactor, self.reslice) = self.slice(sources[0])
        side_ren2.AddActor(sactor)
        self.rw.AddRenderer(side_ren2)

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
        liver_pos = self.liver_actor.GetPosition()
        self.camera.SetFocalPoint(liver_pos)
        self.main_ren.ResetCamera()
        self.main_ren.ResetCameraClippingRange()
        self.show()
        self.rw.Render()
        self.iren.Start()

    def get_sources(self, ct_file, stl_file):
        sources = list()

        # read ct file
        print(ct_file)
        nrrdreader = vtk.vtkNrrdReader()
        nrrdreader.SetFileName(ct_file)
        nrrdreader.Update()
        sources.append(nrrdreader)

        # read STL file
        stlreader = vtk.vtkSTLReader()
        print(stl_file)
        stlreader.SetFileName(stl_file)
        stlreader.Update()
        sources.append(stlreader)

        return sources

    def reverse_sign(self, x):
        if x > 0:
            return -1
        elif x < 0:
            return 1

    def callback_func(self, caller, timer_event):
        # fetch the position data
        position = self.vivecontrol.devices["controller_1"].get_pose_euler()
        # fetch the controller button data
        controller_status = self.vivecontrol.devices["controller_1"].get_controller_inputs(
        )

        txt = ""
        if not hasattr(position, '__iter__'):
            self.needle_actor.GetProperty().SetColor([1, 1, 0])
            print("\r" + "Waiting", end="")
        else:
            for each in position:
                txt += "%.4f" % each
                txt += " "
            print("\r" + txt, end="")

            # toggle objects
            if controller_status['menu_button'] == True and self.volume_visible == True and self.volume_pressed == False:
                self.volume_pressed = True
            elif controller_status['menu_button'] == False and self.volume_visible == True and self.volume_pressed == True:
                self.volume.VisibilityOff()
                self.liver_actor.GetProperty().SetRepresentationToPoints()
                self.volume_visible = False
                self.volume_pressed = False
            elif controller_status['menu_button'] == True and self.volume_visible == False and self.volume_pressed == False:
                self.volume_pressed = True
            elif controller_status['menu_button'] == False and self.volume_visible == False and self.volume_pressed == True:
                self.volume.VisibilityOn()
                self.liver_actor.GetProperty().SetRepresentationToSurface()
                self.volume_visible = True
                self.volume_pressed = False

            # Rotation about axises on the trackpad pression
            # track_pad_border = 0.3
            # zoom in and out need touch but not press the trackpad
            if controller_status['trackpad_touched'] == True and controller_status['trackpad_pressed'] == False and controller_status["grip_button"]:
                distance = self.camera.GetDistance()
                print("distance : " + str(distance))
                if controller_status['trackpad_y'] > self.zoom_var and distance - 500 > 30:
                    self.camera.Dolly(1.01)
                elif controller_status['trackpad_y'] < self.zoom_var and distance < 2500:
                    self.camera.Dolly(0.99)
                self.main_ren.ResetCameraClippingRange()
            # move camera need touch and press the trackpad
            elif controller_status['trackpad_touched'] == True and controller_status['trackpad_pressed'] == True and not controller_status["grip_button"]:
                self.camera.Azimuth(
                    1 * self.reverse_sign(controller_status['trackpad_x']))
                self.camera.Elevation(
                    1 * self.reverse_sign(controller_status['trackpad_y']))
                self.camera.OrthogonalizeViewUp()

            # since the pressure on the trigger is from 0 to 1,
            # I decided compute the trigger strength use 1 - controller_status['trigger']
            # change the color of the needle from (1, 1, 1) to (1, 1 * trigger strength, )
            if controller_status['trigger'] > 0.1:
                print(controller_status)
                trigger_strength = 1 - controller_status['trigger']
                self.needle_actor.GetProperty().SetColor(
                    [1, 1 * trigger_strength, 1 * trigger_strength])
                self.needle_actor.SetPosition(position[0] * -700, position[1]
                                              * 700 - 400, position[2] * -300)
            else:
                # when release the trigger, change the color of needle to white.
                self.needle_actor.GetProperty().SetColor([1, 1, 1])
                self.needle_actor.SetPosition(position[0] * -700, position[1]
                                              * 700 - 400, position[2] * -300)
                self.needle_actor.SetOrientation(
                    -position[5], -position[4], -position[3])

            if controller_status['grip_button']:
                pY = controller_status['trackpad_y']
                print(pY)

                if pY != 0:
                    self.reslice.Update()
                    matrix = self.reslice.GetResliceAxes()
                    # move the center point that we are slicing through
                    center = matrix.MultiplyPoint((0, 0, pY, 1))
                    print(center)
                    if -194 > center[0]:
                        matrix.SetElement(0, 3, -193)
                    elif 194 < center[0]:
                        matrix.SetElement(0, 3, 193)
                    else:
                        matrix.SetElement(0, 3, center[0])

                    matrix.SetElement(1, 3, center[1])
                    matrix.SetElement(2, 3, center[2])

        self.rw.Render()

    def needle(self):
        reader = vtk.vtkSTLReader()
        reader.SetFileName("../data/handler.stl")

        self.collide.SetInputConnection(1, reader.GetOutputPort())
        needle_mapper = vtk.vtkPolyDataMapper()
        needle_mapper.SetInputConnection(reader.GetOutputPort())
        needle_mapper.SetScalarVisibility(0)

        needle_actor = vtk.vtkActor()
        needle_actor.SetMapper(needle_mapper)

        needle_actor.SetPosition(0, 0, 0)
        needle_actor.GetProperty().SetColor([1, 1, 1])
        needle_actor.GetProperty().SetOpacity(1)
        needle_actor.GetProperty().SetInterpolationToPhong()
        needle_actor.GetProperty().SetRepresentationToSurface()

        return needle_actor

    def vtkColor(self):
        color_transfer = vtk.vtkColorTransferFunction()
        color_transfer.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
        color_transfer.AddRGBPoint(-16, 0.73, 0.25, 0.30, 0.49, .61)
        color_transfer.AddRGBPoint(641, .90, .82, .56, .5, 0.0)
        color_transfer.AddRGBPoint(3070, 1.0, 1.0, 1.0, .5, 0.0)
        color_transfer.AddRGBPoint(3071, 0.0, .333, 1.0, .5, 0.0)

        return color_transfer

    def vtkOpacity(self):
        opacity_transfer = vtk.vtkPiecewiseFunction()
        opacity_transfer.AddPoint(-3024, 0, 0.5, 0.0)
        opacity_transfer.AddPoint(-16, 0, .49, .61)
        opacity_transfer.AddPoint(641, .72, .5, 0.0)
        opacity_transfer.AddPoint(3071, .71, 0.5, 0.0)

        return opacity_transfer

    def vtkVolume(self):
        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(self.vtkColor())
        volume_property.SetScalarOpacity(self.vtkOpacity())
        volume_property.SetInterpolationTypeToLinear()
        volume_property.ShadeOn()
        volume_property.SetAmbient(0.1)
        volume_property.SetDiffuse(0.9)
        volume_property.SetSpecular(0.2)
        volume_property.SetSpecularPower(10.0)
        volume_property.SetScalarOpacityUnitDistance(0.8919)

        return volume_property

    def vtkRender(self, pos):
        # Define viewport ranges.
        xmins = [0, .5, 0.5]
        xmaxs = [0.5, 1, 1]
        ymins = [0, 0.5, 0]
        ymaxs = [1, 1, 0.5]

        ren = vtk.vtkRenderer()
        ren.SetViewport(xmins[pos], ymins[pos], xmaxs[pos], ymaxs[pos])

        return ren

    def txtActor(self, Xpos, Ypos, Fontsize, text):
        txt = vtk.vtkTextActor()
        txt.SetInput(text)
        txtprop = txt.GetTextProperty()
        txtprop.SetFontFamilyToArial()
        txtprop.BoldOn()
        txtprop.SetFontSize(Fontsize)
        txtprop.ShadowOn()
        txtprop.SetShadowOffset(4, 4)
        txtprop.SetColor(vtkNamedColors().GetColor3d('White'))
        txt.SetPosition(Xpos, Ypos)

        return txt

    def slice(self, source):
        ctsource = source
        ctsource.SetDataExtent(0, 63, 0, 63, 1, 93)
        ctsource.SetDataSpacing(3.2, 3.2, 1.5)
        ctsource.SetDataOrigin(0.0, 0.0, 0.0)
        ctsource.SetDataScalarTypeToUnsignedShort()
        ctsource.UpdateWholeExtent()

        # Calculate the center of the volume
        ctsource.Update()
        (xMin, xMax, yMin, yMax, zMin, zMax) = ctsource.GetExecutive(
        ).GetWholeExtent(ctsource.GetOutputInformation(0))
        (xSpacing, ySpacing, zSpacing) = ctsource.GetOutput().GetSpacing()
        (x0, y0, z0) = ctsource.GetOutput().GetOrigin()

        center = [x0 + xSpacing * 0.5 * (xMin + xMax),
                  y0 + ySpacing * 0.5 * (yMin + yMax),
                  z0 + zSpacing * 0.5 * (zMin + zMax)]

        # Matrices for axial, coronal, sagittal, oblique view orientations
        axial = vtk.vtkMatrix4x4()
        axial.DeepCopy((1, 0, 0, center[0],
                        0, 1, 0, center[1],
                        0, 0, 1, center[2],
                        0, 0, 0, 1))

        coronal = vtk.vtkMatrix4x4()
        coronal.DeepCopy((1, 0, 0, center[0],
                          0, 0, 1, center[1],
                          0, -1, 0, center[2],
                          0, 0, 0, 1))

        sagittal = vtk.vtkMatrix4x4()
        sagittal.DeepCopy((0, 0, -1, center[0],
                           1, 0, 0, center[1],
                           0, -1, 0, center[2],
                           0, 0, 0, 1))

        oblique = vtk.vtkMatrix4x4()
        oblique.DeepCopy((1, 0, 0, center[0],
                          0, 0.866025, -0.5, center[1],
                          0, 0.5, 0.866025, center[2],
                          0, 0, 0, 1))

        # Extract a slice in the desired orientation
        reslice = vtk.vtkImageReslice()
        reslice.SetInputConnection(ctsource.GetOutputPort())
        reslice.SetOutputDimensionality(2)
        reslice.SetResliceAxes(sagittal)
        reslice.SetInterpolationModeToLinear()

        # Create a greyscale lookup table
        table = vtk.vtkLookupTable()
        table.SetRange(0, 2000)  # image intensity range
        table.SetValueRange(0.0, 1.0)  # from black to white
        table.SetSaturationRange(0.0, 0.0)  # no color saturation
        table.SetRampToLinear()
        table.Build()

        # Map the image through the lookup table
        color = vtk.vtkImageMapToColors()
        color.SetLookupTable(table)
        color.SetInputConnection(reslice.GetOutputPort())

        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(color.GetOutputPort())

        return actor, reslice
