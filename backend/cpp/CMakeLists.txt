cmake_minimum_required(VERSION 3.10)

project(Gitar_Projekt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

add_library(CommonLib STATIC
    common/src/fretboard.cpp
    common/src/input_notes.cpp
    common/src/random.cpp
)

target_include_directories(CommonLib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/common/include)

add_executable(MainOpt main_fingering_optimization/main.cpp)
target_link_libraries(MainOpt PRIVATE CommonLib)

add_executable(PsoOpt pso_fingering_optimization/main.cpp)
target_link_libraries(PsoOpt PRIVATE CommonLib)

add_executable(ViterbiOpt viterbi_fingering_optimization/main.cpp)
target_link_libraries(ViterbiOpt PRIVATE CommonLib)