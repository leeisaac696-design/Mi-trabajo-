[app]
# (str) Title of your application
title = Mi Trabajo

# (str) Package name
package.name = mitrabajo

# (str) Package domain (needed for android/ios packaging)
package.domain = org.mitrabajo

# (str) Source code where main.py live
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,kv,atlas,db

# (str) Application version
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy,pyjnius,reportlab

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (str) Presplash of the application
# presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
# icon.filename = %(source.dir)s/data/icon.png

# (str) Supported Android archs
android.archs = arm64-v8a

# (int) Android API to use
android.api = 36

# (int) Minimum API your APK supports
android.minapi = 24

# (str) Accept Android SDK licenses automatically in CI
android.accept_sdk_license = True

# (str) Python-for-Android branch used by the current Buildozer CI
p4a.branch = develop

# (bool) Allow backup of app data
android.allow_backup = True

# (str) Android application theme
# android.apptheme = "@android:style/Theme.Material.Light.NoActionBar"

[buildozer]
# (int) Log level (0 = error only, 1 = warning, 2 = info, 3 = debug)
log_level = 2

# (bool) Warn when running as root (CI is not root)
warn_on_root = 1
