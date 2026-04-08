#!/bin/bash

# --- ANTI-SUDO SAFEGUARD ---
if [ "$EUID" -eq 0 ]; then
  echo "[ERROR] Do NOT run this script with sudo!"
  echo "Running with sudo strips your virtual environment paths."
  echo "Please run it normally: ./build_deb.sh"
  exit 1
fi

# Exit on any error
set -e

APP_NAME="eventhawk"
APP_VERSION="1.3"
ARCH="amd64"
DEB_DIR="${APP_NAME}_${APP_VERSION}_${ARCH}"

echo "[*] Cleaning up previous builds..."
# We use sudo here just to clean up any root-owned files from your previous attempts
sudo rm -rf build/ dist/ $DEB_DIR/ ${DEB_DIR}.deb

echo "[*] Compiling standalone binary with PyInstaller (running strictly in venv)..."
python3 -m PyInstaller --name $APP_NAME --onedir --windowed \
  --add-data "evtx_tool/profiles/defaults/*.json:evtx_tool/profiles/defaults" \
  --add-data "evtx_tool/data/mappings.json:evtx_tool/data" \
  --add-data "evtx_tool/resources/images/eventhawk_logo.png:evtx_tool/resources/images" \
  --hidden-import "evtx" \
  --collect-all "evtx" \
  --collect-submodules "sentinel" \
  --collect-submodules "evtx_tool" \
  --exclude-module "PyQt5" \
  --exclude-module "PyQt6" \
  --exclude-module "PySide2" \
  evtx_tool.py

echo "[*] Creating Debian package structure..."
mkdir -p $DEB_DIR/DEBIAN
mkdir -p $DEB_DIR/opt/$APP_NAME
mkdir -p $DEB_DIR/usr/bin
mkdir -p $DEB_DIR/usr/share/applications
mkdir -p $DEB_DIR/usr/share/icons/hicolor/256x256/apps

echo "[*] Copying compiled files to /opt/$APP_NAME..."
cp -r dist/$APP_NAME/* $DEB_DIR/opt/$APP_NAME/

echo "[*] Creating executable wrapper in /usr/bin..."
cat << 'EOF' > $DEB_DIR/usr/bin/$APP_NAME
#!/bin/bash
exec /opt/eventhawk/eventhawk "$@"
EOF
chmod +x $DEB_DIR/usr/bin/$APP_NAME

echo "[*] Creating desktop entry..."
cat << EOF > $DEB_DIR/usr/share/applications/${APP_NAME}.desktop
[Desktop Entry]
Version=1.0
Name=EventHawk
Comment=Windows Event Log analysis built for DFIR
Exec=/usr/bin/$APP_NAME gui
Icon=$APP_NAME
Terminal=false
Type=Application
Categories=Utility;Security;
EOF

echo "[*] Copying icon..."
cp evtx_tool/resources/images/eventhawk_logo.png $DEB_DIR/usr/share/icons/hicolor/256x256/apps/${APP_NAME}.png

echo "[*] Generating DEBIAN/control file..."
cat << EOF > $DEB_DIR/DEBIAN/control
Package: $APP_NAME
Version: $APP_VERSION
Section: utils
Priority: optional
Architecture: $ARCH
Maintainer: 0x0z0n
Description: Windows Event Log analysis built for DFIR.
 EventHawk parses Windows Event Logs in parallel using a Rust-backed engine, 
 loads results into a Qt GUI, and provides filters, threat analysis, 
 IOC extraction, and timeline correlation.
EOF

echo "[*] Setting correct permissions (will prompt for password)..."
sudo chown -R root:root $DEB_DIR/
sudo chmod -R 0755 $DEB_DIR/

echo "[*] Building the .deb package..."
sudo dpkg-deb --build $DEB_DIR

echo "[*] Restoring ownership of the generated .deb..."
sudo chown $(whoami):$(whoami) ${DEB_DIR}.deb

echo "[+] Build complete: ${DEB_DIR}.deb generated successfully."