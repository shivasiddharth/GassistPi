# GassistPi

*************************************************  
#LET'S GET STARTED!  
*************************************************  

*************************************************  
#INSTALLING AUDIO CONFIG FILES
*************************************************  
#UPDATE KERNEL  

sudo apt-get update  

sudo apt-get install raspberrypi-kernel

#RESTART PI

#CHOOSE THE AUDIO CONFIGURATION ACCORDING TO YOUR SETUP.  
#(Run the commands till you get .bak notification in the terminal)

#USB DAC users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  

#AIY-HAT users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/configure-driver.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/AIY-HAT/configure-driver.sh  
  
sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/install-alsa-config.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/AIY-HAT/install-alsa-config.sh  

#USB DAC AND HDMI users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
  
#USB DAC AND AUDIO JACK users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
  
#CUSTOM VOICE HAT users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/custom-voice-hat.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/CUSTOM-VOICE-HAT/custom-voice-hat.sh  
  
sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/install-i2s.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/CUSTOM-VOICE-HAT/install-i2s.sh  
  
  
#RESTART PI  

#CHECK THE SPEAKER'S WORKING IN TERMINAL  

speaker-test -t wav  

**********************************************************************  
CONTINUE AFTER SETTING UP AUDIO
**********************************************************************   

#1.download credentials--->.json file  

#2.place the .json file in/home/pi directory  

#3.rename it to assistant--->assistant.json  

#IN TERMINAL:copy paste the following commands one by one  

sudo apt-get update  

sudo apt-get install python3-dev python3-venv  

python3 -m venv env  

env/bin/python -m pip install --upgrade pip setuptools  

source env/bin/activate  

#Install RPi.GPIO for Controlling Devices

pip install RPi.GPIO  

#Get the library and sample code  

python -m pip install --upgrade google-assistant-library  

#INSTALL AUTHORIZATION TOOL  

python -m pip install --upgrade google-auth-oauthlib[tool]  

#RUN THE TOOL(client id already renamed to assistant) just copy paste below  


google-oauthlib-tool --client-secrets /home/pi/assistant.json --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save --headless  

#COPY THE LINK FROM TERMINAL AND PASTE IT IN THE BROWSER  

#COPY THE AUTHORIZATION CODE FROM THE BROWSER AND PASTE IT IN THE TERMINAL  

#TEST BY GIVING SOME VOICE COMMANDS BY TRIGGERING "HEY GOOGLE" FOLLOWED BY YOUR REQUEST
google-assistant-demo

#AFTER EVERYTHING IS WORKING PRESS "CTRL+C" TO COME OUT OF GOOGLE ASSISTANT  

*************************************************  
#Autostart Headless As A Service  
*************************************************  
1. Make the service installer executable  

sudo chmod +x /home/pi/scripts/service-installer.sh  

2. Run the service installer  

sudo /home/pi/scripts/service-installer.sh  

3. Enable the service  

sudo systemctl enable gassistpi.service  

4. Start the service  

sudo systemctl start gassistpi.service  

******RESTART and ENJOY*************************  

************************************************  
#For Neopixel Indicator
************************************************  
#Replace the main.py in src folder with the main.py from Neopixel Indicator Folder.  

#REBOOT  

#Change the Pin numbers in the given sketch according to your board and upload it.  

#Follow the circuit diagram given.  

************************************************  
#Now you have your Google Home Like Indicator  
************************************************  
