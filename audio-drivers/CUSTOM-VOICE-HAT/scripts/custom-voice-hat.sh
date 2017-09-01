#!/bin/bash
#
# Configure Raspberry Pi audio for Custom Voice HAT.

set -o errexit

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 1>&2
   exit 1
fi

cd "$(dirname "${BASH_SOURCE[0]}")/.."

asoundrc=/home/pi/.asoundrc
global_asoundrc=/etc/asound.conf

for rcfile in "$asoundrc" "$global_asoundrc"; do
  if [[ -f "$rcfile" ]] ; then
    echo "Renaming $rcfile to $rcfile.bak..."
    sudo mv "$rcfile" "$rcfile.bak"
  fi
done

sudo cp scripts/asound.conf "$global_asoundrc"
echo "Installing CUSTOM Voice HAT config at $global_asoundrc"
