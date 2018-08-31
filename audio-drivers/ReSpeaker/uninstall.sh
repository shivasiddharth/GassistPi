#!/bin/bash

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 1>&2
   exit 1
fi

is_Raspberry=$(cat /proc/device-tree/model | awk  '{print $1}')
if [ "x${is_Raspberry}" != "xRaspberry" ] ; then
  echo "Sorry, this drivers only works on raspberry pi"
  exit 1
fi

uname_r=$(uname -r)


echo "remove dtbos"
rm  /boot/overlays/seeed-2mic-voicecard.dtbo || true
rm  /boot/overlays/seeed-4mic-voicecard.dtbo || true
rm  /boot/overlays/seeed-8mic-voicecard.dtbo || true

echo "remove alsa configs"
rm -rf  /etc/voicecard/ || true

echo "disabled seeed-voicecard.service "
systemctl disable seeed-voicecard.service 

echo "remove seeed-vocecard"
rm  /usr/bin/seeed-voicecard || true
rm  /lib/systemd/system/seeed-voicecard.service || true

echo "remove dkms"
rm  -rf /var/lib/dkms/seeed-voicecard || true

echo "remove kernel modules"
rm  /lib/modules/${uname_r}/kernel/sound/soc/codecs/snd-soc-wm8960.ko || true
rm  /lib/modules/${uname_r}/kernel/sound/soc/codecs/snd-soc-ac108.ko || true
rm  /lib/modules/${uname_r}/kernel/sound/soc/generic/snd-soc-simple-card.ko || true

echo "------------------------------------------------------"
echo "Please reboot your raspberry pi to apply all settings"
echo "Thank you!"
echo "------------------------------------------------------"
