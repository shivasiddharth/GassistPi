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


cd /home/${USER}/
sudo apt-get update -y
sudo apt-get install python-pip -y
sudo apt-get install libjack-jackd2-dev -y
sudo apt-get install portaudio19-dev libffi-dev libssl-dev -y
sudo pip install pyaudio
sudo apt-get install libatlas-base-dev -y

if [[ $devmodel = "armv7" ]];then
	sed -i 's/__FILE_PATH__/"/home/__USER__/env/bin/python -u /home/__USER__/GassistPi/src/main.py --device_model_id 'saved-model-id'"/g' ${GIT_DIR}/systemd/gassistpi.service
  sed -i 's/saved-model-id/'$modelid'/g' ${GIT_DIR}/systemd/gassistpi.service
else
  sed -i 's/__FILE_PATH__/"/home/__USER__/env/bin/python -u /home/__USER__/GassistPi/src/pushbutton.py --project-id 'created-project-id'  --device-model-id 'saved-model-id'"/g' ${GIT_DIR}/systemd/gassistpi.service
  sed -i 's/created-project-id/'$projid'/g' ${GIT_DIR}/systemd/gassistpi.service
fi

sed -i 's/__USER__/'${USER}'/g' ${GIT_DIR}/systemd/gassistpi.service

sed 's/#.*//' ${GIT_DIR}/Requirements/GassistPi-system-requirements.txt | xargs sudo apt-get install -y

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
