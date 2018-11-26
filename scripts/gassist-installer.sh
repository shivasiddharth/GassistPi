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
echo "Your Model-Id used for the project is: $modelid" >> /home/${USER}/modelid.txt

sudo apt-get update -y
sed 's/#.*//' ${GIT_DIR}/Requirements/GassistPi-system-requirements.txt | xargs sudo apt-get install -y
sudo pip install pyaudio

#Check OS Version
if [[ $(cat /etc/os-release|grep "stretch") ]]; then
	osversion="Stretch"
  echo ""
  echo "===========You are running the installer on Stretch=========="
  echo ""
else
	osversion="Others"
  echo ""
  echo "===========You are advised to use the Stretch version of the OS=========="
  echo "===========Exiting the installer=========="
  echo ""
  exit 1
fi

#Check CPU architecture
if [[ $(uname -m|grep "armv7") ]]; then
	devmodel="armv7"
  echo ""
  echo "===========Your board supports Ok-Google Hotword. You can also trigger the assistant using custom-wakeword=========="
  echo ""
else
	devmodel="armv6"
  echo ""
  echo "==========Your board does not support Ok-Google Hotword. You need to trigger the assistant using pushbutton/custom-wakeword=========="
  echo ""
fi

#Check Board Model
if [[ $(cat /proc/cpuinfo|grep "BCM") ]]; then
	board="Raspberry"
  echo ""
  echo "===========GPIO pins can be used with the assistant=========="
  echo ""
else
	board="Others"
  echo ""
  echo "===========GPIO pins cannot be used by default with the assistant. You need to figure it out by yourselves=========="
  echo ""
fi

if [[ $board = "Others" ]];then
  echo "==========Snowboy wrappers provied with the project are for Raspberry Pi boards. Custom snowboy wrappers need to be compiled for your board=========="
  echo ""
  echo "==========Installing Swig========="
  echo ""
  if [ ! -d /home/${USER}/programs/libraries/swig/ ]; then
    sudo mkdir -p programs/libraries/ && cd programs/libraries
    sudo git clone https://github.com/swig/swig.git
  fi
  cd /home/${USER}/programs/libraries/swig/
  sudo ./autogen.sh
  sudo ./configure
  sudo make
  sudo make install
  echo ""
  echo "==========Compiling custom Snowboy Python3 wrapper=========="
  echo ""
  cd ~/programs
  if [ ! -d /home/${USER}/programs/snowboy/ ]; then
    sudo git clone https://github.com/Kitt-AI/snowboy.git
  fi
  cd /home/${USER}/programs/snowboy/swig/Python3
  sudo make

  if [ -e /home/${USER}/programs/snowboy/swig/Python3/_snowboydetect.so ]; then
    echo "=========Copying Snowboy files to GassistPi directory=========="
    sudo \cp -f ./_snowboydetect.so ${GIT_DIR}/src/_snowboydetect.so
    sudo \cp -f ./snowboydetect.py ${GIT_DIR}/src/snowboydetect.py
  else
    echo "==========Something has gone wrong while compiling the wrappers. Try again or go through the errors above=========="
  fi
fi

cd /home/${USER}/
echo ""
echo ""
echo "==========Changing particulars in service files=========="

if [[ $devmodel = "armv7" ]];then
  echo ""
  echo ""
  echo "==========Changing particulars in service files for Ok-Google hotword=========="
  sed -i '10d' ${GIT_DIR}/systemd/gassistpi.service
  sed -i 's/saved-model-id/'$modelid'/g' ${GIT_DIR}/systemd/gassistpi.service
else
  echo ""
  echo ""
  echo "==========Changing particulars in service files for Pushbutton/Custom-wakeword=========="
  sed -i '9d' ${GIT_DIR}/systemd/gassistpi.service
  sed -i 's/saved-model-id/'$modelid'/g' ${GIT_DIR}/systemd/gassistpi.service
  sed -i 's/created-project-id/'$projid'/g' ${GIT_DIR}/systemd/gassistpi.service
fi

sed -i 's/__USER__/'${USER}'/g' ${GIT_DIR}/systemd/gassistpi.service

python3 -m venv env
env/bin/python -m pip install --upgrade pip setuptools wheel
source env/bin/activate

pip install -r ${GIT_DIR}/Requirements/GassistPi-pip-requirements.txt

if [[ $board = "Raspberry" ]];then
	pip install RPi.GPIO==0.6.3
fi

if [[ $devmodel = "armv7" ]];then
	pip install google-assistant-library==1.0.0
else
  pip install --upgrade --no-binary :all: grpcio
fi

pip install google-assistant-grpc==0.2.0
pip install google-assistant-sdk==0.5.0
pip install google-assistant-sdk[samples]==0.5.0
google-oauthlib-tool --scope https://www.googleapis.com/auth/assistant-sdk-prototype \
          --scope https://www.googleapis.com/auth/gcm \
          --save --headless --client-secrets $credname

echo "Testing the installed google assistant. Make a note of the generated Device-Id"

if [[ $devmodel = "armv7" ]];then
	googlesamples-assistant-hotword --project_id $projid --device_model_id $modelid
else
	googlesamples-assistant-pushtotalk --project-id $projid --device-model-id $modelid
fi
