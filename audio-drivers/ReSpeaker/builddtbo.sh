#dtoverlay -r seeed-2mic-voicecard

dtc -@ -I dts -O dtb -o seeed-2mic-voicecard.dtbo seeed-2mic-voicecard-overlay.dts
dtc -@ -I dts -O dtb -o seeed-4mic-voicecard.dtbo seeed-4mic-voicecard-overlay.dts
dtc -@ -I dts -O dtb -o seeed-8mic-voicecard.dtbo seeed-8mic-voicecard-overlay.dts

# cp *.dtbo /boot/overlays
# dtoverlay seeed-2mic-voicecard
