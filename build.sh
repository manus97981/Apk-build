#!/bin/bash
# Prime Shani — APK Build Script
# Run this on Linux to build the APK

echo ""
echo "======================================"
echo "  PRIME SHANI — APK BUILD SETUP"
echo "======================================"
echo ""

# 1. System dependencies
echo "[1/4] Installing system dependencies..."
sudo apt update -qq
sudo apt install -y \
    git zip unzip \
    openjdk-17-jdk \
    python3 python3-pip \
    build-essential \
    libssl-dev libffi-dev \
    libsqlite3-dev \
    autoconf libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    cmake \
    ffmpeg \
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev \
    2>/dev/null

echo "[2/4] Installing Python packages..."
pip3 install --upgrade pip -q
pip3 install buildozer cython==0.29.37 kivy -q

echo "[3/4] Setting JAVA_HOME..."
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

echo "[4/4] Starting APK build (first build ~20-30 min)..."
echo ""
cd "$(dirname "$0")"
buildozer android debug

echo ""
echo "======================================"
echo "  DONE! APK is in: bin/"
echo "======================================"
