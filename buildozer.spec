[app]

title = Prime Shani

package.name = primeshani
package.domain = org.primeshani

source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,atlas,json,txt

version = 1.0

requirements = python3,kivy==2.3.0,kivymd==1.2.0

orientation = portrait

fullscreen = 0

android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

android.api = 33
android.sdk = 33
android.minapi = 21
android.ndk = 25b

android.archs = arm64-v8a, armeabi-v7a

android.allow_backup = True

android.copy_libs = 1

android.logcat_filters = *:S python:D

presplash.color = #000000

icon.filename = icon.png

android.accept_sdk_license = True

[buildozer]

log_level = 2

warn_on_root = 1
