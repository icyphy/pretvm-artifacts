# Set the system name to QNX
SET(CMAKE_SYSTEM_NAME QNX)

# Set the processor architecture
SET(CMAKE_SYSTEM_PROCESSOR aarch64le)

# Set the compiler architecture
SET(arch gcc_ntoaarch64le)

# Set the compilers
SET(CMAKE_C_COMPILER qcc)
SET(CMAKE_C_COMPILER_TARGET ${arch})
SET(CMAKE_CXX_COMPILER q++)
SET(CMAKE_CXX_COMPILER_TARGET ${arch})

# Set the root path for finding libraries and headers
SET(CMAKE_FIND_ROOT_PATH $ENV{QNX_TARGET};$ENV{QNX_TARGET}/${CMAKE_SYSTEM_PROCESSOR})

# Set the sysroot
SET(CMAKE_SYSROOT $ENV{QNX_TARGET})

# Search for programs in the build host directories
SET(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)

# Search for libraries and headers in the target directories
SET(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
SET(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)

# Set QNX-specific flags
SET(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Vgcc_ntoaarch64le -Os")
SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -Vgcc_ntoaarch64le -Os")

# Set QNX processor for installation
SET(QNX_PROCESSOR aarch64le CACHE STRING "QNX processor architecture")

# Disable PCH for QNX
SET(CMAKE_DISABLE_PRECOMPILE_HEADERS ON)

# Set additional QNX-specific settings
SET(CMAKE_CXX_STANDARD 17)
SET(CMAKE_CXX_STANDARD_REQUIRED ON)
SET(CMAKE_CXX_EXTENSIONS OFF)

# Handle known QNX compiler issues
SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -D_GLIBCXX_USE_CXX11_ABI=0") 