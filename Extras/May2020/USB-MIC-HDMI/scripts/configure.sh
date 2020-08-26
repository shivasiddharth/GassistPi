#!/bin/bash
# Configure to force audio through HDMI


set -o errexit

if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)" 1>&2
   exit 1
fi

set -e

grep -q "force_hdmi_open = 1" /boot/config.txt || \
  echo "force_hdmi_open = 1" >> /boot/config.txt
