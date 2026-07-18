[app]
title = Bukp
package.name = bukp
package.domain = org.bukp

source.dir = .
source.include_exts = py,png,jpg,jpeg,gif,webp,json
source.exclude_dirs = dist,build,.github,__pycache__,screens/__pycache__

version = 1.0.0

requirements = python3,kivy==2.3.0,requests,plyer,pillow

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_NETWORK_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.release_artifact = apk

[buildozer]
log_level = 2
warn_on_root = 1
