find_library(PIGPIO_LIBRARY pigpio)
if(PIGPIO_LIBRARY)
  target_link_libraries(${LF_MAIN_TARGET} PUBLIC ${PIGPIO_LIBRARY})
endif()
