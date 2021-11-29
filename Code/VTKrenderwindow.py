import triad_openvr
import vtk
import sys
import math
from PyQt5 import (Qt, QtGui, QtCore, QtGui, QtWidgets)
from PyQt5.QtWidgets import QAction
from PyQt5.QtGui import QIcon
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonColor import vtkNamedColors
from datetime import date


class RenderWindow(Qt.QMainWindow):

    def __init__(self, ct_file, stl_file, parent=None, ):
        Qt.QMainWindow.__init__(self, parent)
        self.setWindowTitle("VTK Render Window")
        # self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint)
        self.deleteIcon = ".\data\\delete.svg"
        self.logIcon = ".\data\\logo.png"
        self.needle_file = ".\data\\needle.stl"
        self.tumor_file = ".\data\\mass.stl"
        self.focal_point = [-100, -390, 250]

        self.REFRESH_RATE = 180
        self.liver_visible = True
        self.skelton_visible = True
        self.tumor_visible = True
        self.live_is_wireframe = False
        # setup vive controller & check the if controller is in the range
        self.vivecontrol = triad_openvr.triad_openvr()
        self.zoom_var = 0.0
        self.liver_hp = 100

        # logo
        self.setWindowIcon(QtGui.QIcon(self.logIcon))

        tb = self.addToolBar("Logo")
        icon = QtGui.QIcon(self.logIcon)
        new = QAction(icon, "new", self)
        tb.setIconSize(QtCore.QSize(100, 100))
        tb.setStyleSheet("background-color: black; icon-size: 100px 100px;")
        tb.addAction(new)

        # exit = QAction(QtGui.QIcon(self.deleteIcon), "exit", self)
        # exit.triggered.connect(self.close_application)
        # #tb.setStyleSheet("width: 200px")
        # tb.addAction(exit)

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
        self.key_hold = False
        self.iren.CreateRepeatingTimer(int(1 / self.REFRESH_RATE))
        self.iren.AddObserver("TimerEvent", self.callback_func)
        self.iren.AddObserver("KeyPressEvent", self.key_press_func)
        self.iren.AddObserver("KeyReleaseEvent", self.key_release_func)
        self.iren.AddObserver("MouseMoveEvent", self.MouseMoveCallback)
        self.iren.SetRenderWindow(self.rw)

        # get sources
        sources = self.get_sources(ct_file, stl_file)

        # create liver actor to be added later on
        liver_poly_data = sources[1].GetOutput()

        # delaunay3D = vtk.vtkDelaunay3D()
        # delaunay3D.SetInputData(liver_poly_data)

        triangles = vtk.vtkTriangleFilter()
        triangles.SetInputData(liver_poly_data)
        triangles.Update()
        inputPolyData = triangles.GetOutput()

        decimate = vtk.vtkDecimatePro()
        decimate.SetInputData(inputPolyData)
        decimate.SetTargetReduction(0.99)
        decimate.PreserveTopologyOn()
        decimate.Update()
        decimated = vtk.vtkPolyData()
        decimated.ShallowCopy(decimate.GetOutput())

        stlMapper = vtk.vtkPolyDataMapper()
        # stlMapper.SetInputConnection(sources[1].GetOutputPort())
        stlMapper.SetInputData(decimated)
        stlMapper.SetScalarVisibility(0)
        self.liver_actor = vtk.vtkActor()
        self.liver_actor.SetMapper(stlMapper)
        self.liver_actor.RotateX(-90)
        self.liver_actor.GetProperty().SetColor(1, 1, 1)
        self.liver_actor.GetProperty().SetOpacity(1)

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
        needle_reader.SetFileName(self.needle_file)
        # needle_poly = needle_reader.GetOutput()
        # print(needle_poly)
        # needle_reader = vtk.vtkArrowSource()
        # needle_poly = needle_reader.GetOutput()
        # print(needle_poly)
        needle_mapper = vtk.vtkPolyDataMapper()
        needle_mapper.SetInputConnection(needle_reader.GetOutputPort())
        # needle_mapper.SetScalarVisibility(0)
        self.needle_actor = vtk.vtkActor()
        self.needle_actor.SetMapper(needle_mapper)
        self.needle_actor.SetScale(5)
        self.needle_actor.GetProperty().SetColor([1, 1, 1])
        self.needle_actor.GetProperty().SetOpacity(1)
        self.needle_actor.SetOrigin(-16.8, 1.5, 3.0)
        # print(self.needle_actor)
        # print("i = " + str(self.i) + self.needle_actor.GetPoint(self.i))

        # create 3d cursor attached to the tip of the needle
        self.cursor_3d = vtk.vtkCursor3D()
        self.cursor_3d.SetModelBounds(-300, 300, -300, 300, -300, 300)
        # self.cursor_3d.AllOn()
        self.cursor_3d.OutlineOff()
        self.cursor_3d.XShadowsOff()
        self.cursor_3d.YShadowsOff()
        self.cursor_3d.ZShadowsOff()
        self.cursor_3d.TranslationModeOn()
        # self.cursor_3d.Update()
        cursor_mapper = vtk.vtkPolyDataMapper()
        cursor_mapper.SetInputConnection(self.cursor_3d.GetOutputPort())
        self.cursor_actor = vtk.vtkActor()
        self.cursor_actor.GetProperty().SetColor([0.7, 1, 0.4])
        self.cursor_actor.SetMapper(cursor_mapper)

        # load tumor
        tumor_reader = vtk.vtkSTLReader()
        tumor_reader.SetFileName(self.tumor_file)
        tumor_mapper = vtk.vtkPolyDataMapper()
        tumor_mapper.SetInputConnection(tumor_reader.GetOutputPort())
        tumor_mapper.SetScalarVisibility(0)
        self.tumor_actor = vtk.vtkActor()
        self.tumor_actor.SetMapper(tumor_mapper)
        self.tumor_actor.SetPosition(0, 0, 0)
        self.tumor_actor.SetPosition([-200, -390, 200])
        self.tumor_actor.GetProperty().SetColor([0.6, 0, 0])
        self.tumor_actor.GetProperty().SetOpacity(1)
        self.tumor_actor.GetProperty().SetRepresentationToSurface()

        # self.tip = vtk.vtkSphereSource()
        # self.tip.SetRadius(5.0)
        # self.tip.SetCenter(self.needle_actor.GetPosition())
        # tip_mapper = vtk.vtkPolyDataMapper()
        # tip_mapper.SetInputConnection(self.tip.GetOutputPort())
        # self.tip_actor = vtk.vtkActor()
        # self.tip_actor.SetMapper(tip_mapper)
        # self.tip_actor.GetProperty().SetColor([1, 0, 0])
        # # assembly
        # self.assembly = vtk.vtkAssembly()
        # self.assembly.AddPart(self.needle_actor)
        # self.assembly.AddPart(self.tip_actor)

        self.main_ren.AddVolume(self.volume)
        self.main_ren.AddActor(self.liver_actor)
        self.main_ren.AddActor(self.tumor_actor)

        self.main_ren.AddActor(self.needle_actor)
        self.main_ren.AddActor(self.cursor_actor)
        # self.main_ren.AddActor(self.assembly)

        # logo
        # reader = vtk.vtkPNGReader()
        # reader.SetFileName("../data/logo.png")
        # reader.Update()
        # logo = vtk.vtkLogoRepresentation()
        # logo.SetImage(reader.GetOutput())
        # logo.SetPosition(10,10)
        # logo.GetImageProperty().SetOpacity(1.0)
        # logoWidget = vtk.vtkLogoWidget()

        # logo.ProportionalResizeOn()
        # logo.SetPosition(20, 20)
        # logo.SetPosition2(10,10)
        # logoWidget = vtk.vtkLogoWidget()

        # imageActor.SetInputData(reader.GetOutput())

        # Patient Info
        todaystr = date.today().strftime("%m-%d-%Y")
        self.txtActor = vtk.vtkTextActor()
        self.txtActor.GetTextProperty().SetFontSize(40)
        self.txtActor.SetPosition(10, 20)
        self.txtActor.SetInput(
            "Patient name: Alex Smith\nAge: 40 - Male\nDate: "+todaystr)
        self.main_ren.AddActor(self.txtActor)

        # self.main_ren.AddActor(self.txtActor(
        #     2, 980, 15, 'Patient name: Alex Smith'))
        # self.main_ren.AddActor(self.txtActor(2, 960, 15, 'Age: 40 - F'))

        # self.main_ren.AddActor(self.txtActor(2, 940, 15, todaystr))

        # Keyboard
        # self.main_ren.AddActor(self.txtActor(
        #     2, 84, 20, 'Press "L" to turn on/off the LIVER'))
        # self.main_ren.AddActor(self.txtActor(
        #     2, 64, 20, 'Press "S" to turn on/off the SKELETON'))
        # self.main_ren.AddActor(self.txtActor(
        #     2, 44, 20, 'Press "T" to turn on/off the TUMOR'))
        # self.main_ren.AddActor(self.txtActor(
        #     2, 24, 20, 'Press "W" to turn on/off the WIREFRAME for liver'))
        # self.main_ren.AddActor(self.txtActor(
        #     2, 4, 20, 'Press "Alt + F4" for EXIT'))

        # render side window
        print("render side screen 1")
        # side_ren1 = self.vtkRender(1)
        # # side_ren1.AddViewProp(logo)
        # # logo.SetRenderer(side_ren1)
        # self.rw.AddRenderer(side_ren1)

        # logoWidget.SetInteractor(self.iren)
        # logoWidget.SetRepresentation(logo)
        # logoWidget.On()
        # print("NINA")

        # side_ren1.SetViewport(xmins[1], ymins[1], xmaxs[1], ymaxs[1])
        # side_ren1.SetActiveCamera(self.camera)
        # side_ren1.AddActor(self.liver_actor)
        #
        # side_ren1.ResetCamera()
        # side_ren1.ResetCameraClippingRange()

        # side_ren2 = self.vtkRender(2)
        # (actors, reslices) = self.slice(sources[0])
        # side_ren2.AddActor(actors)
        # self.rw.AddRenderer(side_ren2)
        self.slice_index = 0
        (actors, self.reslices) = self.slice(sources[0])
        for i in range(len(actors)):
            side_ren = self.vtkRender(i + 1)
            side_ren.AddActor(actors[i])
            self.rw.AddRenderer(side_ren)

        self.vtkViewportBorder()
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)
        # liver_pos = self.liver_actor.GetPosition()
        # print("liver is at : " + str(self.liver_actor.GetPosition()))
        # self.cursor_3d.SetFocalPoint(liver_pos)
        # print("before" + str(self.camera.GetFocalPoint()))
        # self.camera.SetFocalPoint(liver_pos)

        self.main_ren.ResetCamera()
        self.main_ren.ResetCameraClippingRange()
        self.camera.SetFocalPoint(self.focal_point)
        # print("after" + str(self.camera.GetFocalPoint()))

        self.show()
        self.rw.Render()
        self.iren.Start()

    def close_application(self):
        print("Good Bye!!!")
        sys.exit()

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

    def key_press_func(self, caller, event):
        press_key = self.iren.GetKeySym()

        if press_key == "F1":
            self.slice_index = 0
            self.key_hold = True

        if press_key == "F2":
            self.slice_index = 1
            self.key_hold = True

        if press_key == "F3":
            self.slice_index = 2
            self.key_hold = True

    def key_release_func(self, caller, KeyReleaseEvent):
        released_key = self.iren.GetKeySym()
        if released_key == 'l':
            if self.liver_visible:
                self.liver_actor.VisibilityOff()
                self.liver_visible = False
            else:
                self.liver_actor.VisibilityOn()
                self.liver_visible = True
        elif released_key == 's':
            if self.skelton_visible:
                self.volume.VisibilityOff()
                self.skelton_visible = False
            else:
                self.volume.VisibilityOn()
                self.skelton_visible = True
        elif released_key == 't':
            if self.tumor_visible:
                self.tumor_actor.VisibilityOff()
                self.tumor_visible = False
            else:
                self.tumor_actor.VisibilityOn()
                self.tumor_visible = True
        elif released_key == 'w':
            if self.live_is_wireframe:
                self.liver_actor.GetProperty().SetRepresentationToSurface()
                self.live_is_wireframe = False
            else:
                self.liver_actor.GetProperty().SetRepresentationToWireframe()
                self.live_is_wireframe = True
        if released_key == "F1":
            self.key_hold = False

        if released_key == "F2":
            self.key_hold = False

        if released_key == "F3":
            self.key_hold = False

    def MouseMoveCallback(self, obj, event):
        (lastX, lastY) = self.iren.GetLastEventPosition()
        (mouseX, mouseY) = self.iren.GetEventPosition()
        if self.key_hold:
            reslice = self.reslices[self.slice_index]
            deltaY = mouseY - lastY
            reslice.Update()
            sliceSpacing = reslice.GetOutput().GetSpacing()[2]
            matrix = reslice.GetResliceAxes()
            # move the center point that we are slicing through
            center = matrix.MultiplyPoint((0, 0, sliceSpacing * deltaY, 1))
            matrix.SetElement(0, 3, center[0])
            matrix.SetElement(1, 3, center[1])
            matrix.SetElement(2, 3, center[2])

    def callback_func(self, caller, timer_event):
        # fetch the position data
        position = self.vivecontrol.devices["controller_1"].get_pose_euler()
        position[4] = position[4] + 90
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

            # move the cursor along the needle
            self.cursor_actor.SetPosition(self.needle_actor.GetPosition())

            # Rotation about axises on the trackpad pression
            # track_pad_border = 0.3
            # zoom in and out need touch but not press the trackpad
            if controller_status['trackpad_touched'] == True and controller_status['trackpad_pressed'] == False and controller_status["grip_button"]:
                distance = self.camera.GetDistance()
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

                # self.assembly.SetPosition(position[0] * -700, position[1]
                #                           * 700 - 400, position[2] * -300)
                # self.assembly.SetOrientation(
                #     -position[5], -position[4], -position[3])

            # controller control slice movement
            # if controller_status['grip_button']:
            #     pY = controller_status['trackpad_y']
            #     print(pY)
            #
            #     if pY != 0:
            #         reslice = self.reslices[self.slice_index]
            #         reslice.Update()
            #         matrix = reslice.GetResliceAxes()
            #         # move the center point that we are slicing through
            #         center = matrix.MultiplyPoint((0, 0, pY, 1))
            #         print(center)
            #         if -194 > center[0]:
            #             matrix.SetElement(0, 3, -193)
            #         elif 194 < center[0]:
            #             matrix.SetElement(0, 3, 193)
            #         else:
            #             matrix.SetElement(0, 3, center[0])
            #
            #         matrix.SetElement(1, 3, center[1])
            #         matrix.SetElement(2, 3, center[2])
        # self.needle_actor.GetProperty().SetRepresentationToSurface()
        if self.live_is_wireframe:
            self.liver_actor.GetProperty().SetRepresentationToWireframe()
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
        # Index 0: main view 1: logo view, 2: slice view top 3:slice view front 4: slice view side
        xmins = [0, 0.7, 0.7, 0.7]
        xmaxs = [0.699, 0.999, 0.999, 0.999]
        ymins = [0, 0.601, 0.301, 0.001]
        ymaxs = [1, 0.9, 0.6, 0.3]

        ren = vtk.vtkRenderer()
        ren.SetViewport(xmins[pos], ymins[pos], xmaxs[pos], ymaxs[pos])

        return ren

    def vtkViewportBorder(self):
        xmins = [0.699, 0.999, 0.7, 0.7, 0.7, 0.7, 0, 0, 0]
        xmaxs = [0.7, 1, 0.999, 0.999, 0.999, 0.999, 0.001, 0.699, 0.699]
        ymins = [0, 0, 0.999, 0.6, 0.3, 0, 0, 0.999, 0]
        ymaxs = [1, 1, 1, 0.601, 0.301, 0.001, 1, 1, 0.001]

        for pos in range(9):
            ren = vtk.vtkRenderer()
            ren.SetBackground(85, 85, 85)
            ren.SetViewport(xmins[pos], ymins[pos], xmaxs[pos], ymaxs[pos])
            self.rw.AddRenderer(ren)

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
        # Top view
        axial = vtk.vtkMatrix4x4()
        axial.DeepCopy((1, 0, 0, center[0],
                        0, 1, 0, center[1],
                        0, 0, 1, center[2],
                        0, 0, 0, 1))

        # Front view
        coronal = vtk.vtkMatrix4x4()
        coronal.DeepCopy((1, 0, 0, center[0],
                          0, 0, 1, center[1],
                          0, -1, 0, center[2],
                          0, 0, 0, 1))
        # Side view
        sagittal = vtk.vtkMatrix4x4()
        sagittal.DeepCopy((0, 0, -1, center[0],
                           1, 0, 0, center[1],
                           0, -1, 0, center[2],
                           0, 0, 0, 1))

        # top view
        oblique = vtk.vtkMatrix4x4()
        oblique.DeepCopy((1, 0, 0, center[0],
                          0, 0.866025, -0.5, center[1],
                          0, 0.5, 0.866025, center[2],
                          0, 0, 0, 1))

        viewOri = [axial, coronal, sagittal]
        actors = []
        reslices = []
        for view in viewOri:
            # Extract a slice in the desired orientation
            reslice = vtk.vtkImageReslice()
            reslice.SetInputConnection(ctsource.GetOutputPort())
            reslice.SetOutputDimensionality(2)
            reslice.SetResliceAxes(view)
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

            actors.append(actor)
            reslices.append(reslice)

        return actors, reslices
