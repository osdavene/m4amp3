[app]

# (str) Title of your application
title = Conversor de Audio

# (str) Package name
package.name = audioconverter

# (str) Package domain (needed for android/ios packaging)
package.domain = com.osdavene

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,json

# (list) Application requirements
# comma separated e.g. requirements = sqlite3,kivy
requirements = python3,kivy

# (str) Application versioning
version = 2.0.0

# (list) Permissions
android.permissions = READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE, MANAGE_EXTERNAL_STORAGE

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support.
android.minapi = 21

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (str) python-for-android branch/tag to use (v2024.01.21 para Python 3.11 estable)
p4a.branch = v2024.01.21

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Orientation
orientation = portrait

# (bool) Automatically accept Android SDK licenses
android.accept_sdk_license = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
