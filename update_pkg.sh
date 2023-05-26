#!/bin/sh

echo "--- Run pyinstaller ---"

cd /home/pi/ScadaToRpiGateway
rm -r dist/StartGateWay
pyinstaller -w StartGateWay.py


# Create folders.
echo "--- Recreate pachake folders ---"

cd

[ -e package ] && rm -r package
mkdir -p package/opt
mkdir -p package/usr/share/applications
mkdir -p package/usr/share/icons/hicolor/scalable/apps

echo "--- Copy new files ---"
# Copy files (change icon names, add lines for non-scaled icons)
cp -r ScadaToRpiGateway/dist/StartGateWay package/opt/StartGateWay
cp ScadaToRpiGateway/dist/itelma.svg package/usr/share/icons/hicolor/scalable/apps/StartGateWay.svg
cp ScadaToRpiGateway/dist/StartGateWay.desktop package/usr/share/applications


# Change permissions
echo "--- Change permissions ---"
find package/opt/StartGateWay -type f -exec chmod 644 -- {} +
find package/opt/StartGateWay -type d -exec chmod 755 -- {} +
find package/usr/share -type f -exec chmod 644 -- {} +
chmod +x package/opt/StartGateWay/StartGateWay

cd

echo "--- Install ---"
fpm -C package -s dir -t deb -n "StartGateWay" -v 0.1.0 -p StartGateWay.deb
sudo dpkg -i StartGateWay.deb

rm StartGateWay.deb
