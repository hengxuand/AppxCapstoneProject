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
        self.deleteIcon = ".\data\\delete.svg"
        self.logIcon = ".\data\\logo.png"
        self.needle_file = ".\data\\needle.stl"
        self.tumor_file = ".\data\\mass.stl"
        self.focal_point = [-100, -390, 250]
        self.REFRESH_RATE = 180
        self.liver_visible = True
        self.skelton_visible = True
        self.tumor_visible = True
        self.liver_is_wireframe = False

        # setup vive controller & check the if controller is in the range
        self.vivecontrol = triad_openvr.triad_openvr()
        self.zoom_var = 0.0
        self.liver_hp = 100

        # logo
        self.setWindowIcon(QtGui.QIcon(self.logIcon))

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
        self.key_lock = False
        self.iren.CreateRepeatingTimer(int(1 / self.REFRESH_RATE))
        self.iren.AddObserver("TimerEvent", self.callback_func)
        self.iren.AddObserver("KeyPressEvent", self.key_press_func)
        self.iren.AddObserver("KeyReleaseEvent", self.key_release_func)
        self.iren.AddObserver("MouseMoveEvent", self.MouseMoveCallback)
        self.iren.SetRenderWindow(self.rw)

        # get sources
        sources = self.get_sources(ct_file, stl_file)

        # logo actor
        logo_reader = vtk.vtkPNGReader()
        logo_reader.SetFileName(self.logIcon)
        logo_reader.Update()
        logo_resize = vtk.vtkImageResize()
        logo_resize.SetInputData(logo_reader.GetOutput())
        logo_resize.SetOutputDimensions(200, 170, 1)
        logo_resize.Update()

        image_mapper = vtk.vtkImageMapper()
        image_mapper.SetInputData(logo_resize.GetOutput())
        image_mapper.Update()
        image_mapper.SetColorLevel(128.0)
        image_mapper.SetColorWindow(256.0)

        self.logo_actor = vtk.vtkActor2D()
        self.logo_actor.SetMapper(image_mapper)
        self.logo_actor.SetPosition(30, 1930)

        # create liver actor to be added later on
        liver_poly_data = sources[1].GetOutput()

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
        needle_mapper = vtk.vtkPolyDataMapper()
        needle_mapper.SetInputConnection(needle_reader.GetOutputPort())
        self.needle_actor = vtk.vtkActor()
        self.needle_actor.SetMapper(needle_mapper)
        self.needle_actor.SetScale(5)
        self.needle_actor.GetProperty().SetColor([1, 1, 1])
        self.needle_actor.GetProperty().SetOpacity(1)
        self.needle_actor.SetOrigin(-16.8, 1.5, 3.0)

        # create 3d cursor attached to the tip of the needle
        self.cursor_3d = vtk.vtkCursor3D()
        self.cursor_3d.SetModelBounds(-300, 300, -300, 300, -300, 300)
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

        self.main_ren.AddVolume(self.volume)
        self.main_ren.AddActor(self.liver_actor)
        self.main_ren.AddActor(self.tumor_actor)

        self.main_ren.AddActor(self.logo_actor)
        self.main_ren.AddActor(self.needle_actor)
        self.main_ren.AddActor(self.cursor_actor)

        # Patient Info
        todaystr = date.today().strftime("%m-%d-%Y")
        self.txtActor = vtk.vtkTextActor()
        self.txtActor.GetTextProperty().SetFontSize(40)
        self.txtActor.SetPosition(10, 20)
        self.txtActor.SetInput(
            "Patient name: Alex Smith\nAge: 40 - Male\nDate: "+todaystr)
        self.main_ren.AddActor(self.txtActor)

        # 2d cursor
        self.cursors_x = [[300.0, 0.0, 1.0], [-300.0, 0.0, 1.0]]
        self.cursors_y = [[0.0, 300.0, 1.0], [0.0, -300.0, 1.0]]
        self.cursors_x_actor = []
        self.cursors_y_actor = []

        for i in range(3):
            cursor_line_x = vtk.vtkLineSource()
            cursor_line_x.SetPoint1(self.cursors_x[0])
            cursor_line_x.SetPoint2(self.cursors_x[1])
            cursor_x_mapper = vtk.vtkPolyDataMapper()
            cursor_x_mapper.SetInputConnection(cursor_line_x.GetOutputPort())
            cursor_x_actor = vtk.vtkActor()
            cursor_x_actor.SetMapper(cursor_x_mapper)
            cursor_x_actor.GetProperty().SetLineWidth(4)
            cursor_x_actor.GetProperty().SetColor([0.7, 1, 0.4])
            self.cursors_x_actor.append(cursor_x_actor)
            cursor_line_y = vtk.vtkLineSource()
            cursor_line_y.SetPoint1(self.cursors_y[0])
            cursor_line_y.SetPoint2(self.cursors_y[1])
            cursor_y_mapper = vtk.vtkPolyDataMapper()
            cursor_y_mapper.SetInputConnection(cursor_line_y.GetOutputPort())
            cursor_y_actor = vtk.vtkActor()
            cursor_y_actor.SetMapper(cursor_y_mapper)
            cursor_y_actor.GetProperty().SetLineWidth(2)
            cursor_y_actor.GetProperty().SetColor([0.7, 1, 0.4])
            self.cursors_y_actor.append(cursor_y_actor)

        # render side window
        print("render side screen 1")
        self.slice_index = 0
        (actors, self.reslices) = self.slice(sources[0])
        print(len(actors))
        for i in range(len(actors)):
            side_ren = self.vtkRender(i + 1)
            side_ren.AddActor(actors[i])
            side_ren.AddActor(self.cursors_x_actor[i])
            side_ren.AddActor(self.cursors_y_actor[i])
            self.rw.AddRenderer(side_ren)

        self.vtkViewportBorder()
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.main_ren.ResetCamera()
        self.main_ren.ResetCameraClippingRange()
        self.camera.SetFocalPoint(self.focal_point)

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
            if self.liver_is_wireframe:
                self.liver_actor.GetProperty().SetRepresentationToSurface()
                self.liver_is_wireframe = False
            else:
                self.liver_actor.GetProperty().SetRepresentationToWireframe()
                self.liver_is_wireframe = True
        if released_key == "F1":
            self.key_hold = False

        if released_key == "F2":
            self.key_hold = False

        if released_key == "F3":
            self.key_hold = False

        if released_key == "F4":
            # print(self.key_lock)
            if self.key_lock:
                self.key_lock = False
            else:
                self.key_lock = True

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
            print("/n")
            print(self.needle_actor.GetPosition())
            print(center)
            print("/n")
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
                # print(controller_status)
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

            # print(self.key_lock)
            if self.key_lock:
                center = self.needle_actor.GetPosition()
                print("center : " + str(center))
                # move the 2d cursors
                self.cursors_x_actor[0].SetPosition(
                    0, (center[2] - 150) * -1, 1)
                self.cursors_y_actor[0].SetPosition(
                    center[0], 0, 1)
                self.cursors_x_actor[1].SetPosition(
                    0, (center[1] + 450), 1)
                self.cursors_y_actor[1].SetPosition(
                    center[0], 0, 1)
                self.cursors_x_actor[2].SetPosition(
                    0, center[1] + 450, 1)
                self.cursors_y_actor[2].SetPosition(
                    (center[2] - 150) * -1, 0, 1)

                for i in range(3):
                    reslice = self.reslices[i]
                    matrix = reslice.GetResliceAxes()
                    mcenter = matrix.MultiplyPoint((0, 0, 0, 1))

                    if i == 0:
                        matrix.SetElement(0, 3, mcenter[0])
                        matrix.SetElement(1, 3, mcenter[1])
                        matrix.SetElement(2, 3, center[1])
                    if i == 1:
                        matrix.SetElement(0, 3, mcenter[0])
                        matrix.SetElement(1, 3, -center[2])
                        matrix.SetElement(2, 3, mcenter[2])
                    if i == 2:
                        matrix.SetElement(0, 3, center[0])
                        matrix.SetElement(1, 3, mcenter[1])
                        matrix.SetElement(2, 3, mcenter[2])
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

        if self.liver_is_wireframe:
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
        # xmins = [0.002, 0.501, 0.002, 0.501]
        # xmaxs = [0.499, 0.998, 0.499, 0.998]
        # ymins = [0.501, 0.501, 0.002, 0.002]
        # ymaxs = [0.998, 0.998, 0.499, 0.499]

        # xmins = [0, 0.7, 0.7, 0.7]
        # xmaxs = [0.699, 0.999, 0.999, 0.999]
        # ymins = [0, 0.6676, 0.3343, 0.001]
        # ymaxs = [1, 0.9999, 0.6666, 0.3333]

        xmins = [0.001, 0.5, 0.5, 0.75]
        xmaxs = [0.499, 0.999, 0.749, 0.999]
        ymins = [0.001, 0.6, 0.001, 0.001]
        ymaxs = [0.999, 0.999, 0.599, 0.599]

        ren = vtk.vtkRenderer()
        ren.SetViewport(xmins[pos], ymins[pos], xmaxs[pos], ymaxs[pos])

        return ren

    def vtkViewportBorder(self):
        # xmins = [0, 0, 0, 0, 0.499, 0.998]
        # xmaxs = [1, 1, 1, 0.002, 0.501, 1]
        # ymins = [0, 0.499, 0.998, 0, 0, 0]
        # ymaxs = [0.002, 0.501, 1, 1, 1, 1]

        # xmins = [0.699, 0.999, 0.7, 0.7, 0.7, 0.7, 0, 0, 0]
        # xmaxs = [0.7, 1, 0.999, 0.999, 0.999, 0.999, 0.001, 0.699, 0.699]
        # ymins = [0, 0, 0.999, 0.6664, 0.3333, 0, 0, 0.999, 0]
        # ymaxs = [1, 1, 1, 0.6676, 0.3343, 0.001, 1, 1, 0.001]

        xmins = [0, 0.499, 0.999, 0, 0, 0.749, 0.5]
        xmaxs = [0.001, 0.5, 1, 1, 1, 0.75, 1]
        ymins = [0, 0, 0, 0, 0.999, 0.001, 0.599]
        ymaxs = [1, 1, 1, 0.001, 1, 0.6, 0.6]

        for pos in range(7):
            ren = vtk.vtkRenderer()
            ren.SetBackground(0.4, 0.4, 0.4)
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
