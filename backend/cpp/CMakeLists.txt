cmake_minimum_required(VERSION 3.15)

project(Gitar_Projekt LANGUAGES CXX)

if(MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

add_library(CommonLib STATIC
    common/src/fretboard.cpp
    common/src/input_notes.cpp
    common/src/random.cpp
    common/src/benchmark.cpp
)

target_include_directories(CommonLib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/common/include)

add_executable(MainOpt
    common/src/app_main.cpp
    main_fingering_optimization/algorithm.cpp
    main_fingering_optimization/note_position.cpp
    main_fingering_optimization/optimization.cpp
    )
target_link_libraries(MainOpt PRIVATE CommonLib)
set_target_properties(MainOpt PROPERTIES
    OUTPUT_NAME "main"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/main_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/main_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/main_fingering_optimization"
)

add_executable(PsoOpt
    common/src/app_main.cpp
    pso_fingering_optimization/algorithm.cpp
    pso_fingering_optimization/note_position.cpp
    pso_fingering_optimization/particle.cpp
    pso_fingering_optimization/pso.cpp
    )
target_link_libraries(PsoOpt PRIVATE CommonLib)
set_target_properties(PsoOpt PROPERTIES
    OUTPUT_NAME "main"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/pso_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/pso_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/pso_fingering_optimization"
)

add_executable(ViterbiOpt
    common/src/app_main.cpp
    viterbi_fingering_optimization/algorithm.cpp
    viterbi_fingering_optimization/note_position.cpp
    viterbi_fingering_optimization/viterbi.cpp
    )
target_link_libraries(ViterbiOpt PRIVATE CommonLib)
set_target_properties(ViterbiOpt PROPERTIES
    OUTPUT_NAME "main"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/viterbi_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/viterbi_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/viterbi_fingering_optimization"
)

add_executable(MainPlusViterbiOpt
    common/src/app_main.cpp
    main_plus_viterbi_fingering_optimization/algorithm.cpp
    main_plus_viterbi_fingering_optimization/note_position.cpp
    main_plus_viterbi_fingering_optimization/optimization.cpp
    )
target_link_libraries(MainPlusViterbiOpt PRIVATE CommonLib)
set_target_properties(MainPlusViterbiOpt PROPERTIES 
    OUTPUT_NAME "main"
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/main_plus_viterbi_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}/main_plus_viterbi_fingering_optimization"
    RUNTIME_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}/main_plus_viterbi_fingering_optimization"
)