

# Bare Google Assistant for Linux Systems   
*******************************************************************************************************************************
### **If you like the work, find it useful and if you would like to get me a :coffee: :smile:** [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7GH3YDCHZ36QN)

### Do not raise an Issue request for Non-Issue stuff. For Non-Issue Help and Interaction use gitter [![Join the chat at https://gitter.im/publiclab/publiclab](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/GassistPi/Lobby/)  

*******************************************************************************************************************************

### NOTE: "${USER}" will automatically take your username. No need to change that. Just copy pasting the following commands on terminal will work.  

*************************************************
## **FIRST STEP- CLONE the PROJECT on to Pi**   
*************************************************
1. Open the terminal and execute the following  

```
sudo apt-get install git  
sudo apt-get install alsa-utils   
git clone https://github.com/shivasiddharth/GassistPi -b Just-Google-Assistant
```

*************************************************  
## **INSTALL AUDIO CONFIG FILES**
*************************************************  
1. Update OS     

```
sudo apt-get update
```

2. Restart Pi  and change directory
```
cd /home/${USER}/   
```

3. Choose the audio configuration according to your setup.   
**Non-Raspberry Pi users, choose the USB-DAC option.    
The speaker-test command is used to initialize alsa, so please do not skip that.  
AIY-HAT and CUSTOM-HAT users, please reboot the Pi at places mentioned, else it will lead to audio and taskbar issues.**  

3.1. USB DAC or USB Sound CARD users,  
```
sudo chmod +x ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
sudo ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh
speaker-test  
```

3.2. AIY-HAT users,  
```
sudo chmod +x ./GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
sudo ./GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
sudo reboot  
cd /home/${USER}/  
sudo chmod +x ./GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
sudo ./GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
speaker-test  
```

3.3. USB MIC AND HDMI users,  
```
sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/configure.sh  
sudo ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/configure.sh  
sudo reboot  
cd /home/${USER}/  
sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
sudo ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
speaker-test  
```

3.4. USB MIC AND AUDIO JACK users,  
```  
sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
sudo ./GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
speaker-test  
```       
3.5. CUSTOM VOICE HAT users,  
```
sudo chmod +x ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh  
sudo ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh
sudo reboot  
cd /home/${USER}/  
sudo chmod +x ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
sudo ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
speaker-test   
```

3.6. RESPEAKER HAT users,  
```
git clone https://github.com/shivasiddharth/seeed-voicecard
cd ./seeed-voicecard/  
sudo ./install.sh  
sudo reboot   
speaker-test     
```  

**Those using any other DACs or HATs install the cards as per the manufacturer's guide
 and then you can try using the USB-DAC config file after changing the hardware ids**        

4. Restart Pi

5. Check the speaker using the following command    

```
speaker-test -t wav  
```  

**********************************************************************  
## **CONTINUE after SETTING UP AUDIO**
**********************************************************************   

1. Follow the instructions [here](https://developers.google.com/assistant/sdk/guides/library/python/embed/config-dev-project-and-account) to Configure a Developer Project and Account Settings. Then follow this [guide](https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device) to register the device and obtain the credentials file. Refer to the video below for step by step guidelines.  

<a href="http://www.youtube.com/watch?feature=player_embedded&v=dMNtmp8z52M
" target="_blank"><img src="http://img.youtube.com/vi/dMNtmp8z52M/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>


2. Place the credentials file in/home/${USER}/ directory **DO NOT RENAME**  

3. Use the one-line installer for installing Google Assistant    

3.1 Change directory
```
cd /home/${USER}/      
```

3.2 Make the installer Executable  
```
sudo chmod +x ./GassistPi/scripts/gassist-installer.sh
```

3.3 Execute the installer. **When Prompted, enter your Google Cloud console Project-Id, A name for your Assistant and the Full Name of your credentials file, including the json extension.**  
```
sudo  ./GassistPi/scripts/gassist-installer.sh
```  

4. Copy the google assistant authentication link from terminal and authorize using your google account  

5. Copy the authorization code from browser onto the terminal and press enter    

6. After successful authentication, the Google Assistant Demo test will automatically start. At the start, the volume might be low, the assistant volume is independent of the Pi volume, so increase the volume by using "Hey Google, Set volume to maximum" command.

7. After verifying the working of assistant, close and exit the terminal    


*************************************************  
## **HEADLESS AUTOSTART on BOOT SERVICE SETUP**  
*************************************************  
1. Open the service files in the /GassistPi/systemd/ directory and verify your project and model ids and save the file.

2. Change directory
```
cd /home/${USER}   
```

3. Make the service installer executable  

```
sudo chmod +x ./GassistPi/scripts/service-installer.sh  
```  

4. Run the service installer  

```
sudo ./GassistPi/scripts/service-installer.sh    
```  

5. Enable the service    
```
sudo systemctl enable gassistpi.service  
```  

6. Start the service     
```
sudo systemctl start gassistpi.service  
```  

**RESTART and ENJOY**  

### MANUALLY START THE ASSISTANT

At any point of time, if you wish to manually start the assistant:
Open a terminal and execute the following:
```
/home/${USER}/env/bin/python -u /home/${USER}/GassistPi/src/main.py --device_model_id 'replace this with the model id'

```

Insert your Project Id and Model Id in quotes in the mentioned places      

### DISABLING AUTO-START ON BOOT      

At any point of time, if you wish to stop the auto start of the assistant:      

Open a terminal and execute the following:     
```
sudo systemctl stop gassistpi.service  
sudo systemctl disable gassistpi.service   
```    
