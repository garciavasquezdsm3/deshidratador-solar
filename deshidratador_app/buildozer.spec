[app]
title = Deshidratador Solar
package.name = deshidratadorsolar
package.domain = org.midominio

source.dir = .
source.include_exts = py,kv,png,jpg,atlas

version = 0.1

requirements = python3,kivy==2.3.0,bleak,pyjnius,android

orientation = portrait
fullscreen = 0

# Permisos necesarios para BLE en Android 12+ y versiones anteriores
android.permissions = BLUETOOTH,BLUETOOTH_ADMIN,BLUETOOTH_SCAN,BLUETOOTH_CONNECT,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION

android.api = 33
android.minapi = 24
android.archs = arm64-v8a,armeabi-v7a

[buildozer]
log_level = 2
warn_on_root = 1
