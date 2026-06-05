[app]
title = Prime Shani
package.name = primeshani
package.domain = org.primeshani
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 1.0

# kivymd removed — reduces size from 40MB to ~12MB
requirements = python3,kivy==2.3.0

orientation = portrait
fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a

android.allow_backup = True
android.accept_sdk_license = True
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
