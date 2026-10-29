cmake_minimum_required(VERSION 3.16)
project(galahad_description)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf launch config meshes rviz
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
