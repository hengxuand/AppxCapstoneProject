import triad_openvr
import vtk
import time
from PyQt5 import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkCommonColor import vtkNamedColors


class RenderWindow(Qt.QMainWindow):

    def __init__(self, ct_file, stl_file, parent=None, ):
        Qt.QMainWindow.__init__(self, parent)
        self.setWindowTitle("VTK Render Window")

        self.REFRESH_RATE = 60
        # setup vive controller & check the if controller is in the range
        self.vivecontrol = triad_openvr.triad_openvr()

        while(True):
            position = self.vivecontrol.devices["controller_1"].get_pose_euler(
            )

            start = time.time()
            message = ""
            if not hasattr(position, '__iter__'):
                message = "Waiting for controller."
                print("\r" + message, end="")
                sleep_time = 1/self.REFRESH_RATE-(time.time()-start)
                if sleep_time > 0:
                    time.sleep(sleep_time)
            else:
                print("\r" + "Start to initial VTK window.", end="")
                break

        print("VTK Render Window Start")
        # setup Qt frame
        self.frame = Qt.QFrame()
        self.frame.setMinimumSize(1024, 800)
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

        self.needle_actor = self.needle()

        self.iren.CreateRepeatingTimer(int(1 / self.REFRESH_RATE))
        self.iren.AddObserver("TimerEvent", self.callback_func)
        self.iren.SetRenderWindow(self.rw)

        # Define viewport ranges.
        xmins = [0, .5]
        xmaxs = [0.5, 1]
        ymins = [0, 0.5]
        ymaxs = [1, 1]

        # get sources
        sources = self.get_sources(ct_file, stl_file)
        # create tumor actor to be added later on
        stlMapper = vtk.vtkPolyDataMapper()
        stlMapper.SetInputConnection(sources[1].GetOutputPort())
        stlMapper.SetScalarVisibility(0)
        tumor_actor = vtk.vtkActor()
        tumor_actor.SetMapper(stlMapper)
        tumor_actor.RotateX(-90)

        # render main screen
        print("render main screen")
        main_ren = vtk.vtkRenderer()
        self.rw.AddRenderer(main_ren)
        main_ren.SetViewport(xmins[0], ymins[0], xmaxs[0], ymaxs[0])

        camera = main_ren.GetActiveCamera()
        camera.Azimuth(30)
        camera.Elevation(30)

        color_transfer_function = vtk.vtkColorTransferFunction()
        color_transfer_function.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
        color_transfer_function.AddRGBPoint(-16,
                                            0.73, 0.25, 0.30, 0.49, .61)
        color_transfer_function.AddRGBPoint(
            641, .90, .82, .56, .5, 0.0)
        color_transfer_function.AddRGBPoint(
            3070, 1.0, 1.0, 1.0, .5, 0.0)
        color_transfer_function.AddRGBPoint(
            3071, 0.0, .333, 1.0, .5, 0.0)

        opacity_transfer_function = vtk.vtkPiecewiseFunction()
        opacity_transfer_function.AddPoint(-3024, 0, 0.5, 0.0)
        opacity_transfer_function.AddPoint(-16, 0, .49, .61)
        opacity_transfer_function.AddPoint(641, .72, .5, 0.0)
        opacity_transfer_function.AddPoint(3071, .71, 0.5, 0.0)

        volMapper = vtk.vtkGPUVolumeRayCastMapper()
        volMapper.SetInputConnection(sources[0].GetOutputPort())

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
        volume.RotateX(-90)
        main_ren.AddVolume(volume)
        main_ren.AddActor(self.needle_actor)
        main_ren.AddActor(tumor_actor)

        main_ren.ResetCamera()
        main_ren.ResetCameraClippingRange()

        # render side window
        print("render side screen 1")
        side_ren1 = vtk.vtkRenderer()
        self.rw.AddRenderer(side_ren1)
        side_ren1.SetViewport(xmins[1], ymins[1], xmaxs[1], ymaxs[1])
        side_ren1.SetActiveCamera(camera)
        side_ren1.AddActor(tumor_actor)

        side_ren1.ResetCamera()
        side_ren1.ResetCameraClippingRange()

        # for i in range(2):
        #     print("render screen " + str(i))
        #     ren = vtk.vtkRenderer()
        #     self.rw.AddRenderer(ren)
        #     ren.SetViewport(xmins[i], ymins[i], xmaxs[i], ymaxs[i])
        #     ren.SetActiveCamera(camera)
        #     # Share the camera between viewports.
        #     if i == 0:
        #         camera = ren.GetActiveCamera()
        #         camera.Azimuth(30)
        #         camera.Elevation(30)

        #         color_transfer_function = vtk.vtkColorTransferFunction()
        #         color_transfer_function.AddRGBPoint(-3024, 0, 0, 0, 0.5, 0.0)
        #         color_transfer_function.AddRGBPoint(-16,
        #                                             0.73, 0.25, 0.30, 0.49, .61)
        #         color_transfer_function.AddRGBPoint(
        #             641, .90, .82, .56, .5, 0.0)
        #         color_transfer_function.AddRGBPoint(
        #             3070, 1.0, 1.0, 1.0, .5, 0.0)
        #         color_transfer_function.AddRGBPoint(
        #             3071, 0.0, .333, 1.0, .5, 0.0)

        #         opacity_transfer_function = vtk.vtkPiecewiseFunction()
        #         opacity_transfer_function.AddPoint(-3024, 0, 0.5, 0.0)
        #         opacity_transfer_function.AddPoint(-16, 0, .49, .61)
        #         opacity_transfer_function.AddPoint(641, .72, .5, 0.0)
        #         opacity_transfer_function.AddPoint(3071, .71, 0.5, 0.0)

        #         volMapper = vtk.vtkGPUVolumeRayCastMapper()
        #         volMapper.SetInputConnection(sources[0].GetOutputPort())

        #         volume_property = vtk.vtkVolumeProperty()
        #         volume_property.SetColor(color_transfer_function)
        #         volume_property.SetScalarOpacity(opacity_transfer_function)
        #         volume_property.SetInterpolationTypeToLinear()
        #         volume_property.ShadeOn()
        #         volume_property.SetAmbient(0.1)
        #         volume_property.SetDiffuse(0.9)
        #         volume_property.SetSpecular(0.2)
        #         volume_property.SetSpecularPower(10.0)
        #         volume_property.SetScalarOpacityUnitDistance(0.8919)

        #         volume = vtk.vtkVolume()
        #         volume.SetMapper(volMapper)
        #         volume.SetProperty(volume_property)
        #         volume.RotateX(-90)
        #         ren.AddVolume(volume)
        #         ren.AddActor(self.needle_actor)
        #     else:
        #         ren.SetActiveCamera(camera)

        #     stlMapper = vtk.vtkPolyDataMapper()
        #     stlMapper.SetInputConnection(sources[1].GetOutputPort())
        #     stlMapper.SetScalarVisibility(0)

        #     # Create an actor
        #     actor = vtk.vtkActor()
        #     actor.SetMapper(stlMapper)
        #     actor.RotateX(-90)
        #     ren.AddActor(actor)

        #     ren.ResetCamera()
        #     ren.ResetCameraClippingRange()

        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

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

            # since the pressure on the trigger is from 0 to 1,
            # I decided compute the trigger strength use 1 - controller_status['trigger']
            # change the color of the needle from (1, 1, 1) to (1, 1 * trigger strength, )
            if(controller_status['trigger'] > 0.1):
                print(controller_status)
                trigger_strength = 1-controller_status['trigger']
                self.needle_actor.GetProperty().SetColor(
                    [1, 1*trigger_strength, 1*trigger_strength])
            else:
                # when release the trigger, change the color of needle to white.
                self.needle_actor.GetProperty().SetColor([1, 1, 1])
                self.needle_actor.SetPosition(position[0] * -700, position[1]
                                              * 700 - 400, position[2] * -300)
                self.needle_actor.SetOrientation(
                    -position[5], -position[4], -position[3])

            self.rw.Render()

    def needle(self):
        reader = vtk.vtkSTLReader()
        reader.SetFileName("./data/handler.stl")

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

        # sample needle
        # cylinder = vtk.vtkCylinderSource()
        # cylinder.SetCenter(0.0, 0.0, 0.0)
        # cylinder.Update()
        #
        # cylinder_mapper = vtk.vtkPolyDataMapper()
        # cylinder_mapper.SetInputConnection(cylinder.GetOutputPort())
        # c_actor = vtk.vtkActor()
        # c_actor.SetMapper(cylinder_mapper)
        #
        # c_actor.SetPosition(0, 0, 0)
        # c_actor.GetProperty().SetColor(vtkNamedColors().GetColor3d('Goldenrod'))
        # c_actor.GetProperty().SetOpacity(1)
        # c_actor.GetProperty().SetInterpolationToPhong()
        # c_actor.GetProperty().SetRepresentationToSurface()
        # c_actor.RotateY(30)

        return needle_actor
