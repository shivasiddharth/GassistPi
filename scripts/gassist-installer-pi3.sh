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
YES_ANSWER=1
NO_ANSWER=2
QUIT_ANSWER=3
parse_user_input()
{
  if [ "$1" = "0" ] && [ "$2" = "0" ] && [ "$3" = "0" ]; then
    return
  fi
  while [ true ]; do
    Options="["
    if [ "$1" = "1" ]; then
      Options="${Options}y"
      if [ "$2" = "1" ] || [ "$3" = "1" ]; then
        Options="$Options/"
      fi
    fi
    if [ "$2" = "1" ]; then
      Options="${Options}n"
      if [ "$3" = "1" ]; then
        Options="$Options/"
      fi
    fi
    if [ "$3" = "1" ]; then
      Options="${Options}quit"
    fi
    Options="$Options]"
    read -p "$Options >> " USER_RESPONSE
    USER_RESPONSE=$(echo $USER_RESPONSE | awk '{print tolower($0)}')
    if [ "$USER_RESPONSE" = "y" ] && [ "$1" = "1" ]; then
      return $YES_ANSWER
    else
      if [ "$USER_RESPONSE" = "n" ] && [ "$2" = "1" ]; then
        return $NO_ANSWER
      else
        if [ "$USER_RESPONSE" = "quit" ] && [ "$3" = "1" ]; then
          printf "\nGoodbye.\n\n"
          exit
        fi
      fi
    fi
    printf "Please enter a valid response.\n"
  done
}
clear
echo ""
read -r -p "Enter the your full credential file name including .json extension: " credname
echo ""
read -r -p "Enter the your Google Cloud Console Project-Id: " projid
echo ""
read -r -p "Enter a nickname for your device: " nickname
echo ""
echo "Credentials file name is >> $credname"
echo ""
echo "Project id is >> $projid"
echo ""
echo "Nickname for your device is >> $nickname"
echo ""
echo ""
echo "Is this information correct?"
echo ""
echo ""
parse_user_input 1 1 0
USER_RESPONSE=$?
if [ "$USER_RESPONSE" = "$YES_ANSWER" ]; then
  return
elif [ "$USER_RESPONSE" = "$NO_ANSWER" ]; then
  read -r -p "Enter the your full credential file name including .json extension: " credname
  echo ""
  read -r -p "Enter the your Google Cloud Console Project-Id: " projid
  echo ""
  read -r -p "Enter a nickname for your device: " nickname
  echo ""
fi
set -o errexit

scripts_dir="$(dirname "${BASH_SOURCE[0]}")"

# make sure we're running as the owner of the checkout directory
RUN_AS="$(ls -ld "$scripts_dir" | awk 'NR==1 {print $3}')"
if [ "$USER" != "$RUN_AS" ]
then
    echo "This script must run as $RUN_AS, trying to change user..."
    exec sudo -u $RUN_AS $0
fi

modelid=$projid-$(date +%F)

cd /home/pi/
sudo pip3 install mps-youtube youtube-dl
sudo apt-get install vlc -y
mpsyt set player vlc, set playerargs ,exit
sudo apt-get install elinks -y
sudo apt-get update -y
sudo apt-get install python3-dev python3-venv -y
sudo apt-get install portaudio19-dev libffi-dev libssl-dev -y
sudo apt-get install libttspico0 libttspico-utils libttspico-data -y
python3 -m venv env
env/bin/python -m pip install --upgrade pip setuptools
source env/bin/activate
pip install RPi.GPIO
pip install pyaudio
pip install aftership
pip install feedparser
pip install kodi-json
python -m pip install --upgrade google-assistant-library
python -m pip install --upgrade google-assistant-sdk
python -m pip install --upgrade google-assistant-sdk[samples]
python -m pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2
google-oauthlib-tool --client-secrets /home/pi/$credname --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save --headless
googlesamples-assistant-devicetool register-model --manufacturer "Pi Foundation" \
          --product-name "GassistPi" --nickname $nickname --model $modelid
echo "The model-id used for the project is $modelid " >> /home/pi/modelid.txt
echo "Testing the installed google assistant"
googlesamples-assistant-hotword --project_id $projid --device_model_id $modelid
