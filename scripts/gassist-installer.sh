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
echo "Your Model-Id: $modelid Project-Id: $projid used for this project" >> /home/${USER}/modelid.txt

sudo apt-get update -y
sed 's/#.*//' ${GIT_DIR}/Requirements/GassistPi-system-requirements.txt | xargs sudo apt-get install -y
sudo pip install pyaudio

#Check OS Version
echo ""
#Check CPU architecture
if [[ $(uname -m|grep "armv7") ]] || [[ $(uname -m|grep "x86_64") ]]; then
	devmodel="armv7"
  echo ""
  echo "Your board supports voice controlled Google Assistant."
  echo ""
else
	devmodel="armv6"
  echo ""
  echo "Your board does not support voice control."
  echo ""
  exit 1
fi


cd /home/${USER}/
echo ""
echo ""

python3 -m venv env
env/bin/python -m pip install --upgrade pip setuptools wheel
source env/bin/activate

pip install -r ${GIT_DIR}/Requirements/GassistPi-pip-requirements.txt

pip install google-assistant-library==1.1.0
pip install google-assistant-sdk==0.6.0
pip install google-assistant-sdk[samples]==0.6.0
google-oauthlib-tool --scope https://www.googleapis.com/auth/assistant-sdk-prototype \
          --scope https://www.googleapis.com/auth/gcm \
          --save --headless --client-secrets $credname
echo ""
echo ""
echo "Finished installing Google Assistant........."
