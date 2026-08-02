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

add_executable(MainOpt
    main_fingering_optimization/main.cpp
    main_fingering_optimization/note_position.cpp
    main_fingering_optimization/optimization.cpp
    )
target_link_libraries(MainOpt PRIVATE CommonLib)

add_executable(PsoOpt
    pso_fingering_optimization/main.cpp
    pso_fingering_optimization/note_position.cpp
    pso_fingering_optimization/particle.cpp
    pso_fingering_optimization/pso.cpp
    )
target_link_libraries(PsoOpt PRIVATE CommonLib)

add_executable(ViterbiOpt
    viterbi_fingering_optimization/main.cpp
    viterbi_fingering_optimization/note_position.cpp
    viterbi_fingering_optimization/viterbi.cpp
    )
target_link_libraries(ViterbiOpt PRIVATE CommonLib)