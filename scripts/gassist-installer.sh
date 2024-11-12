#!/bin/bash
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
set -o errexit

scripts_dir="$(dirname "${BASH_SOURCE[0]}")"
GIT_DIR="$(realpath $(dirname ${BASH_SOURCE[0]})/..)"

# make sure we're running as the owner of the checkout directory
RUN_AS="$(ls -ld "$scripts_dir" | awk 'NR==1 {print $3}')"
if [ "$USER" != "$RUN_AS" ]
then
    echo "This script must run as $RUN_AS, trying to change user..."
    exec sudo -u $RUN_AS $0
fi
clear
echo ""
read -r -p "Enter the your full credential file name including the path and .json extension: " credname
echo ""
read -r -p "Enter the your Google Cloud Console Project-Id: " projid
echo ""
read -r -p "Enter the modelid that was generated in the actions console: " modelid
echo ""


sudo apt-get update -y
sed 's/#.*//' ${GIT_DIR}/Requirements/GassistPi-system-requirements.txt | xargs sudo apt-get install -y


#Check OS Version
echo ""
echo "Checking OS Compatability"
echo ""
if [[ $(cat /etc/os-release|grep "raspbian") ]]; then
  if [[ $(cat /etc/os-release|grep "stretch") ]]; then
    osversion="Raspbian Stretch"
    echo ""
    echo "You are running the installer on Stretch="
    echo ""
  elif [[ $(cat /etc/os-release|grep "buster") ]]; then
    osversion="Raspbian Buster"
    echo ""
    echo "You are running the installer on Buster"
    echo ""
  elif [[ $(cat /etc/os-release|grep "bullseye") ]]; then
    osversion="Raspbian Bullseye"
    echo ""
    echo "You are running the installer on Bullseye"
    echo ""
  else
    osversion="Other Raspbian"
    echo ""
    echo "You are advised to use the Stretch or Buster or Bullseye version of the OS"
    echo "Exiting the installer="
    echo ""
    exit 1
  fi
elif [[ $(cat /etc/os-release|grep "armbian") ]]; then
  if [[ $(cat /etc/os-release|grep "stretch") ]]; then
    osversion="Armbian Stretch"
    echo ""
    echo "You are running the installer on Stretch"
    echo ""
  elif [[ $(cat /etc/os-release|grep "buster") ]]; then
    osversion="Armbian Buster"
    echo ""
    echo "You are running the installer on Buster"
    echo ""
  elif [[ $(cat /etc/os-release|grep "bullseye") ]]; then
    osversion="Armbian Bullseye"
    echo ""
    echo "You are running the installer on Bullseye"
    echo ""
  else
    osversion="Other Armbian"
    echo ""
    echo "You are advised to use the Stretch version of the OS"
    echo "Exiting the installer="
    echo ""
    exit 1
  fi
elif [[ $(cat /etc/os-release|grep "osmc") ]]; then
  osmcversion=$(grep VERSION_ID /etc/os-release)
  osmcversion=${osmcversion//VERSION_ID=/""}
  osmcversion=${osmcversion//'"'/""}
  osmcversion=${osmcversion//./-}
  osmcversiondate=$(date -d $osmcversion +%s)
  export LC_ALL=C.UTF-8
  export LANG=C.UTF-8
  if (($osmcversiondate > 1512086400)); then
    osversion="OSMC Stretch"
    echo ""
    echo "Compatible OSMC version"
    echo ""
  else
    osversion="Other OSMC"
    echo ""
    echo "You are advised to use atleast the Stretch version of the OS"
    echo "Exiting the installer="
    echo ""
    exit 1
  fi
elif [[ $(cat /etc/os-release|grep "ubuntu") ]]; then
  if [[ $(cat /etc/os-release|grep "bionic") ]]; then
    osversion="Ubuntu Bionic"
    echo ""
    echo "You are running the installer on Bionic"
    echo ""
  else
    osversion="Other Ubuntu"
    echo ""
    echo "You are advised to use the Bionic version of the OS"
    echo "Exiting the installer="
    echo ""
    exit 1
  fi
fi

#Check CPU architecture
if [[ $(uname -m|grep "armv7") ]] || [[ $(uname -m|grep "x86_64") ]] || [[ $(uname -m|grep "armv8") ]] || [[ $(uname -m|grep "aarch64") ]]; then
	devmodel="armv7"
  echo ""
  echo "Your board supports Ok-Google Hotword. You can also trigger the assistant using custom-wakeword"
  echo ""
else
	devmodel="armv6"
  echo ""
  echo "=Your board does not support Ok-Google Hotword. You need to trigger the assistant using pushbutton/custom-wakeword"
  echo ""
fi

#Check Board Model
if [[ $(cat /proc/cpuinfo|grep "BCM") ]]; then
	board="Raspberry"
  echo ""
  echo "GPIO pins can be used with the assistant"
  echo ""
else
	board="Others"
  echo ""
  echo "GPIO pins cannot be used by default with the assistant. You need to figure it out by yourselves"
  echo ""
fi

echo ""
cd /home/${USER}/

python3 -m venv env
env/bin/python -m pip install --upgrade pip setuptools wheel
source env/bin/activate

pip install -r ${GIT_DIR}/Requirements/GassistPi-pip-requirements.txt
pip install git+https://github.com/shivasiddharth/pafy.git

if [[ $board = "Raspberry" ]] && [[ $osversion != "OSMC Stretch" ]];then
	pip install RPi.GPIO==0.7.1a4
  if [ -f /lib/udev/rules.d/91-pulseaudio-rpi.rules ] ; then
      sudo rm /lib/udev/rules.d/91-pulseaudio-rpi.rules
  fi
fi

if [[ $devmodel = "armv7" ]];then
	pip install google-assistant-library==1.1.0
else
  pip install --upgrade --no-binary :all: grpcio
fi

pip install google-assistant-grpc==0.3.0
pip install google-assistant-sdk==0.6.0
pip install google-assistant-sdk[samples]==0.6.0
google-oauthlib-tool --scope https://www.googleapis.com/auth/assistant-sdk-prototype \
          --save --client-secrets $credname

echo ""
echo ""
echo ""
if [ -f /home/${USER}/modelid.txt ] ; then
  echo "Auto modification of the service file is not feasible. Manually check your username, project id and model id....."
else
  echo "Changing particulars in service files......"
  if [[ $devmodel = "armv7" ]];then
    echo ""
    echo ""
    echo "Changing particulars in service files for Ok-Google hotword......."
    sed -i '/pushbutton.py/d' ${GIT_DIR}/systemd/gassistpi.service
    sed -i 's/created-project-id/'$projid'/g' ${GIT_DIR}/systemd/gassistpi.service
    sed -i 's/saved-model-id/'$modelid'/g' ${GIT_DIR}/systemd/gassistpi.service
  else
    echo ""
    echo ""
    echo "Changing particulars in service files for Pushbutton/Custom-wakeword......."
    sed -i '/main.py/d' ${GIT_DIR}/systemd/gassistpi.service
    sed -i 's/created-project-id/'$projid'/g' ${GIT_DIR}/systemd/gassistpi.service
    sed -i 's/saved-model-id/'$modelid'/g' ${GIT_DIR}/systemd/gassistpi.service
  fi
  sed -i 's/__USER__/'${USER}'/g' ${GIT_DIR}/systemd/gassistpi.service
fi
echo ""
echo ""

echo "Your Model-Id: $modelid Project-Id: $projid used for this project" >> /home/${USER}/modelid.txt
echo ""
echo ""
echo "Finished installing Google Assistant......."
echo ""
echo ""
echo "Please reboot........"
