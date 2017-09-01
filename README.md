****** # GassistPi

*************************************************  
******LET'S GET STARTED!  
*************************************************  

*************************************************  
******INSTALLING AUDIO CONFIG FILES
*************************************************  
1. UPDATE KERNEL  

sudo apt-get update  

sudo apt-get install raspberrypi-kernel

2. RESTART PI

3. CHOOSE THE AUDIO CONFIGURATION ACCORDING TO YOUR SETUP.  
   (Run the commands till you get .bak notification in the terminal)

3.1. USB DAC users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  

3.2. AIY-HAT users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/configure-driver.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/AIY-HAT/configure-driver.sh  
  
sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/install-alsa-config.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/AIY-HAT/install-alsa-config.sh  

3.3. USB DAC AND HDMI users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
  
3.4. USB DAC AND AUDIO JACK users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
  
3.5. CUSTOM VOICE HAT users,  
sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/custom-voice-hat.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/CUSTOM-VOICE-HAT/custom-voice-hat.sh  
  
sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/install-i2s.sh  
sudo /home/pi/GassistPi/audio-drivers/USB-DAC/CUSTOM-VOICE-HAT/install-i2s.sh  
  
  
4. RESTART PI  

5. CHECK THE SPEAKER'S WORKING IN TERMINAL  

speaker-test -t wav  

**********************************************************************  
******CONTINUE AFTER SETTING UP AUDIO
**********************************************************************   

1. Download credentials--->.json file  

2. Place the .json file in/home/pi directory  

3. Rename it to assistant--->assistant.json  

4. IN TERMINAL:copy paste the following commands one by one  

sudo apt-get update  

sudo apt-get install python3-dev python3-venv  

python3 -m venv env  

env/bin/python -m pip install --upgrade pip setuptools  

source env/bin/activate  

5. Install RPi.GPIO for Controlling Devices

pip install RPi.GPIO  

6. Get the library and sample code  

python -m pip install --upgrade google-assistant-library  

7. INSTALL AUTHORIZATION TOOL  

python -m pip install --upgrade google-auth-oauthlib[tool]  

8. RUN THE TOOL(client id already renamed to assistant) just copy paste below  

google-oauthlib-tool --client-secrets /home/pi/assistant.json --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save --headless  

9. COPY THE LINK FROM TERMINAL AND PASTE IT IN THE BROWSER  

10. COPY THE AUTHORIZATION CODE FROM THE BROWSER AND PASTE IT IN THE TERMINAL  

11. TEST BY GIVING SOME VOICE COMMANDS BY TRIGGERING "HEY GOOGLE" FOLLOWED BY YOUR REQUEST

google-assistant-demo

12. AFTER EVERYTHING IS WORKING PRESS "CTRL+C" TO COME OUT OF GOOGLE ASSISTANT  

*************************************************  
******Autostart Headless As A Service  
*************************************************  
1. Make the service installer executable  

sudo chmod +x /home/pi/GassistPi/scripts/service-installer.sh  

2. Run the service installer  

sudo /home/pi/GassistPi/scripts/service-installer.sh  

3. Enable the service  

sudo systemctl enable gassistpi.service  

4. Start the service  

sudo systemctl start gassistpi.service  

******RESTART and ENJOY  

************************************************  
******For Neopixel Indicator
************************************************  
#Replace the main.py in src folder with the main.py from Neopixel Indicator Folder.  

#REBOOT  

#Change the Pin numbers in the given sketch according to your board and upload it.  

#Follow the circuit diagram given.  

************************************************  
******Now you have your Google Home Like Indicator  
************************************************  
