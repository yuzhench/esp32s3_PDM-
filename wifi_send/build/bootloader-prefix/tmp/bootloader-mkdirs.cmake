# Distributed under the OSI-approved BSD 3-Clause License.  See accompanying
# file Copyright.txt or https://cmake.org/licensing for details.

cmake_minimum_required(VERSION 3.5)

file(MAKE_DIRECTORY
  "/home/yuzhen/esp/esp-idf/components/bootloader/subproject"
  "/home/yuzhen/esp/wifi_send/build/bootloader"
  "/home/yuzhen/esp/wifi_send/build/bootloader-prefix"
  "/home/yuzhen/esp/wifi_send/build/bootloader-prefix/tmp"
  "/home/yuzhen/esp/wifi_send/build/bootloader-prefix/src/bootloader-stamp"
  "/home/yuzhen/esp/wifi_send/build/bootloader-prefix/src"
  "/home/yuzhen/esp/wifi_send/build/bootloader-prefix/src/bootloader-stamp"
)

set(configSubDirs )
foreach(subDir IN LISTS configSubDirs)
    file(MAKE_DIRECTORY "/home/yuzhen/esp/wifi_send/build/bootloader-prefix/src/bootloader-stamp/${subDir}")
endforeach()
if(cfgdir)
  file(MAKE_DIRECTORY "/home/yuzhen/esp/wifi_send/build/bootloader-prefix/src/bootloader-stamp${cfgdir}") # cfgdir has leading slash
endif()
