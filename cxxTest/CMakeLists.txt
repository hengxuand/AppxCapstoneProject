cmake_minimum_required(VERSION 3.3 FATAL_ERROR)

project(OpenVROrientedCylinder)

find_package(VTK COMPONENTS 
  vtkCommonColor
  vtkCommonCore
  vtkCommonDataModel
  vtkCommonTransforms
  vtkFiltersGeneral
  vtkFiltersSources
  vtkInteractionStyle
  vtkRenderingContextOpenGL2
  vtkRenderingCore
  vtkRenderingFreeType
  vtkRenderingGL2PSOpenGL2
  vtkRenderingOpenGL2
  vtkRenderingOpenVR
  QUIET
)

if (NOT VTK_FOUND)
  message("Skipping OpenVROrientedCylinder: ${VTK_NOT_FOUND_MESSAGE}")
  return ()
endif()
message (STATUS "VTK_VERSION: ${VTK_VERSION}")
if (VTK_VERSION VERSION_LESS "8.90.0")
  # old system
  include(${VTK_USE_FILE})
  add_executable(OpenVROrientedCylinder MACOSX_BUNDLE OpenVROrientedCylinder.cxx )
  target_link_libraries(OpenVROrientedCylinder PRIVATE ${VTK_LIBRARIES})
else ()
  # include all components
  add_executable(OpenVROrientedCylinder MACOSX_BUNDLE OpenVROrientedCylinder.cxx )
  target_link_libraries(OpenVROrientedCylinder PRIVATE ${VTK_LIBRARIES})
  # vtk_module_autoinit is needed
  vtk_module_autoinit(
    TARGETS OpenVROrientedCylinder
    MODULES ${VTK_LIBRARIES}
    )
endif ()