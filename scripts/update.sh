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

# make sure we're running as the owner of the checkout directory
RUN_AS="$(ls -ld "$scripts_dir" | awk 'NR==1 {print $3}')"
if [ "$USER" != "$RUN_AS" ]
then
    echo "This script must run as $RUN_AS, trying to change user..."
    exec sudo -u $RUN_AS $0
fi

sudo apt-get update -y
sudo apt-get install jq -y

#Check CPU architecture
if [[ $(uname -m|grep "armv7") ]]; then
  devmodel="armv7"
else
  devmodel="armv6"
fi

echo "Checking for updates................"
echo ""
wget "http://raw.githubusercontent.com/shivasiddharth/GassistPi/master/version" -O /tmp/version

AvailableSDKVersion=($(jq '.Version.SDK' /tmp/version))
AvailableFeaturesVersion=($(jq '.Version.Features' /tmp/version))
AvailableRevisionVersion=($(jq '.Version.Revision' /tmp/version))

CurrentSDKVersion=($(jq '.Version.SDK' /home/${USER}/GassistPi/version))
CurrentFeaturesVersion=($(jq '.Version.Features' /home/${USER}/GassistPi/version))
CurrentRevisionVersion=($(jq '.Version.Revision' /home/${USER}/GassistPi/version))

if ((AvailableSDKVersion > CurrentSDKVersion)) || ((AvailableFeaturesVersion > CurrentFeaturesVersion)) || ((AvailableRevisionVersion > CurrentRevisionVersion)); then
  echo "A new update is available........."
  echo ""
  echo ""
else
  echo "The project is already uptodate........"
  echo ""
  echo ""
  exit 1
fi

if ((AvailableSDKVersion > CurrentSDKVersion)); then
  Updatetype="SDK"
  echo "You have a SDK update.........."
  echo ""
  echo ""
elif ((AvailableFeaturesVersion > CurrentFeaturesVersion)); then
  Updatetype="Feature"
  echo "You have a Feature update.........."
  echo ""
  echo ""
elif ((AvailableRevisionVersion > CurrentRevisionVersion)); then
  Updatetype="Revision"
  echo "You have updates to the scripts or bug fixes.........."
  echo ""
  echo ""
fi

if ps ax | grep -v grep | grep gassistpi > /dev/null
then
    echo "Google Assistant Voice Service is running, stopping it for updating the project.............."
    echo ""
    echo ""
    sudo systemctl stop gassistpi.service
else
    echo "Service is not running, proceeding to update the project.............."
    echo ""
    echo ""
fi

echo "Backing up your old project..............."
echo ""
echo ""
backupfoldername=(GassistPi.bak-$(date +%F))

sudo cp -a /home/${USER}/GassistPi/ /home/${USER}/${backupfoldername}/

echo "Updating the scripts..............."
echo ""
echo ""

sudo rm -rf /home/${USER}/GassistPi/
git clone https://github.com/shivasiddharth/GassistPi

sudo \cp -f /home/${USER}/${backupfoldername}/src/_snowboydetect.so /home/${USER}/GassistPi/src/_snowboydetect.so
sudo \cp -f /home/${USER}/${backupfoldername}/src/snowboydetect.py /home/${USER}/GassistPi/src/snowboydetect.py

cd /home/${USER}/

if [[ $Updatetype = "Revision" ]];then
  echo "Finsihed updating......."
  echo "Restart your service using: sudo systemctl restart gassistpi.service"
  echo ""
  echo ""
  exit 1
elif [[ $Updatetype = "Feature" ]] || [[ $Updatetype = "SDK" ]];then
  echo "Installing new dependencies......................"
  sed 's/#.*//' /home/${USER}/GassistPi/Requirements/GassistPi-system-requirements.txt | xargs sudo apt-get install -y
  source env/bin/activate
  pip install -r /home/${USER}/GassistPi/Requirements/GassistPi-pip-requirements.txt
  echo ""
  echo ""
fi

if [[ $Updatetype != "SDK" ]];then
  echo "Finsihed updating......."
  echo "Restart your service using: sudo systemctl restart gassistpi.service"
  echo ""
  echo ""
  exit 1
else
  echo "Updating the SDK............"
  echo ""
  echo ""
  if [[ $devmodel = "armv7" ]];then
    pip install google-assistant-library --upgrade
  else
    pip install --upgrade --no-binary :all: grpcio
  fi
  pip install google-assistant-grpc --upgrade
  pip install google-assistant-sdk --upgrade
  pip install google-assistant-sdk[samples] --upgrade
  echo ""
  echo ""
  echo "Finsihed updating the SDK......."
  echo "Restart your service using: sudo systemctl restart gassistpi.service"
  exit 1
fi
