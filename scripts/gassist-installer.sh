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


#check device architecture
if [[ $(uname -m|grep "armv7") ]]; then
	devmodel="armv7"
else
	devmodel="armv6"
fi

# make sure we're running as the owner of the checkout directory
RUN_AS="$(ls -ld "$scripts_dir" | awk 'NR==1 {print $3}')"
if [ "$USER" != "$RUN_AS" ]
then
    echo "This script must run as $RUN_AS, trying to change user..."
    exec sudo -u $RUN_AS $0
fi
INFO_FILE="/home/${USER}/gassistant-credentials.info"

clear
if [ -f $INFO_FILE ]
then
    . $INFO_FILE
fi

if [[ $credname != "" ]]
then

   credmsg="If your credentials file name is $credname then press enter. Else, enter your full credential file name including .json extension: "
else
    credmsg="Enter your full credential file name including .json extension: "
fi

if [[ $project_id != "" ]]
then
    projidmsg="If your Project-Id is $project_id then press enter. Else, enter your Google Cloud Console Project-Id: "

else
    projidmsg="Enter your Google Cloud Console Project-Id: "
fi

if [[ $prodname != "" ]]
then
    prodmsg="If your Product name is $prodname then press enter. Else, enter a product name for your device (product name should not have space in between): "
else
    prodmsg="Enter a product name for your device (product name should not have space in between): "
fi



echo ""
echo -e $credmsg
read -r tmp

if [[ $tmp != "" ]]
then 
	credname=$tmp
fi
echo ""
echo -e $projidmsg
read -r tmp
if [[ $tmp != "" ]]
then 
	project_id=$tmp
fi
echo ""
echo -e $prodmsg
read -r tmp
if [[ $tmp != "" ]]
then 
	prodname=$tmp
fi
echo ""


device_model_id=$project_id-$(date +%Y%m%d%H%M%S )
echo "" > $INFO_FILE
echo "credname='$credname'" >> $INFO_FILE
echo "project_id='$project_id'" >> $INFO_FILE
echo "prodname='$prodname'" >> $INFO_FILE
echo "device_model_id='$device_model_id'" >> $INFO_FILE


cd /home/${USER}



if hash apt-get >/dev/null 2>&1;then
  sudo apt-get update -y
  sed 's/#.*//' ${GIT_DIR}/Requirements/GassistPi-system-requirements.txt | xargs sudo apt-get install -y
elif hash pacman >/dev/null 2>&1;then
#  sudo pacman -Sy
  sed 's/#.*//' ${GIT_DIR}/Requirements/GassistPi-system-requirements-archlinux.txt | xargs sudo pacman -S --noconfirm --needed
fi

if [ ! -d /home/${USER}/.config/mpv/scripts/ ]; then
  mkdir -p /home/${USER}/.config/mpv/scripts/
fi
if [ -f ${GIT_DIR}/src/end.lua ]; then
  cp ${GIT_DIR}/src/end.lua /home/${USER}/.config/mpv/scripts/end.lua
fi
if [ -f ${GIT_DIR}/src/mpv.conf ]; then
  cp ${GIT_DIR}/src/mpv.conf /home/${USER}/.config/mpv/mpv.conf
fi


python3 -m venv env
env/bin/python -m pip install --upgrade pip setuptools wheel
source env/bin/activate

pip install -r ${GIT_DIR}/Requirements/GassistPi-pip-requirements.txt

if [[ $devmodel = "armv7" ]];then
	pip install google-assistant-library==0.1.0
fi

pip install google-assistant-grpc==0.1.0
pip install google-assistant-sdk==0.4.2
pip install google-assistant-sdk[samples]==0.4.2
pip install google-auth==1.3.0	google-auth-httplib2==0.0.3 google-auth-oauthlib==0.2.0
google-oauthlib-tool --client-secrets /home/${USER}/$credname --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save --headless
googlesamples-assistant-devicetool register-model --manufacturer "Pi Foundation" \
          --product-name $prodname --type LIGHT --model $device_model_id
          
echo "Testing the installed google assistant. Make a note of the generated Device-Id"

if [[ $devmodel = "armv7" ]];then
	googlesamples-assistant-hotword --project_id $project_id --device_model_id $device_model_id
else
	googlesamples-assistant-pushtotalk --project-id $project_id --device-model-id $device_model_id
fi


