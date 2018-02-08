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
GIT_DIR="$( dirname $(cd "$(dirname "$0")" ; pwd -P) )"

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
info_file="/home/${USER}/gassistant-credentials.info"

clear
if [ -f $info_file ]
then
    . $info_file
fi

if [ -n $credname ]
then
    credmsg="Enter your full credential file name including .json extension(If your credentials file name is $credname then press enter): "
else
    credmsg="Enter your full credential file name including .json extension: "
fi

if [ -n $projid ]
then
    projidmsg="Enter your Google Cloud Console Project-Id(If your Project-Id is $projid then press enter): "
else
    projidmsg="Enter your Google Cloud Console Project-Id: "
fi

if [ -n $prodname ]
then
    prodmsg="Enter a product name for your device (product name should not have space in between)\n(If your Product name is $prodname then press enter): "
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
	projid=$tmp
fi
echo ""
echo -e $prodmsg
read -r tmp
if [[ $tmp != "" ]]
then 
	prodname=$tmp
fi
echo ""


modelid=$projid-$(date +%Y%m%d%H%M%S )
echo "" > $info_file
echo "credname='$credname'" >> $info_file
echo "projid='$projid'" >> $info_file
echo "prodname='$prodname'" >> $info_file
echo "modelid='$modelid'" >> $info_file

cd /home/${USER}


sudo apt-get update -y

sed 's/#.*//' ${GIT_DIR}/Requirements/GassistPi-system-requirements.txt | xargs sudo apt-get install -y
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
          --product-name $prodname --type LIGHT --model $modelid
echo "Testing the installed google assistant. Make a note of the generated Device-Id"

if [[ $devmodel = "armv7" ]];then
	googlesamples-assistant-hotword --project_id $projid --device_model_id $modelid
else
	googlesamples-assistant-pushtotalk --project-id $projid --device-model-id $modelid
fi


