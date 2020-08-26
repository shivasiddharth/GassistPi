#!/bin/bash
#
# Configure Raspberry Pi audio for USB MIC and onboard 3.5mm Jack.

set -o errexit

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 1>&2
   exit 1
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

asoundrc=/home/${SUDO_USER}/.asoundrc
global_asoundrc=/etc/asound.conf
audioconfig=/home/${SUDO_USER}/audiosetup

for rcfile in "$asoundrc" "$global_asoundrc"; do
  if [[ -f "$rcfile" ]] ; then
    echo "Renaming $rcfile to $rcfile.bak..."
    sudo mv "$rcfile" "$rcfile.bak"
  fi
done

if [ -f $audioconfig ] ; then
    sudo rm $audioconfig
fi

echo 'USB-MIC-JACK' >> $audioconfig

sudo cp scripts/asound.conf "$global_asoundrc"
sudo cp scripts/.asoundrc "$asoundrc"
echo "Installing USB MIC and onboard 3.5mm Jack config"
