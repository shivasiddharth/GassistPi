
# GassistPi -- Google Assistant for all Raspberry Pi Boards  
**WORKS WITH Pi3 as well as Pi Zero**  

# Features:  
**1. Headless auto start on boot with multiple wakeword activation trigger**    
**2. Locally Control GPIOs without IFTTT, API.AI, ACTIONS.**  
**3. Startup audio and audio feedback for wakeword detection.**   
**4. Safe shutdown RPi using voice command.**  

# Features coming soon:
**1. Mute button.**  


*************************************************  
**LET'S GET STARTED!**  
*************************************************  

*************************************************  
**INSTALL AUDIO CONFIG FILES**
*************************************************  
1. Update OS and Kernel    

```
sudo apt-get update  
sudo apt-get install raspberrypi-kernel  
``` 

2. Restart Pi  

3. Choose the audio configuration according to your setup.    
   (Run the commands till you get .bak notification in the terminal)

  3.1. USB DAC users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
  sudo /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh 
  ``` 

  3.2. AIY-HAT users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
  sudo /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
  
  sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
  sudo /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
  ```

  3.3. USB MIC AND HDMI users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
  sudo /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
  ```
  
  3.4. USB MIC AND AUDIO JACK users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
  sudo /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh 
  ``` 
  
  3.5. CUSTOM VOICE HAT users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
  sudo /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
  
  sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh  
  sudo /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh 
  ``` 
  
**Those Using HDMI/Onboard Jack, make sure to force the audio**  
```
sudo raspi-config  
```
Select advanced options, then audio and choose to force audio

**Those using any other DACs or HATs install the cards as per the manufacturer's guide
and then you can try using the USB-DAC config file after changing the hardware ids**        

4. Restart Pi

5. Check the speaker using the following command    

```
speaker-test -t wav  
```  

**********************************************************************  
**CONTINUE AFTER SETTING UP AUDIO**
**********************************************************************   

1. Download credentials--->.json file  

2. Place the .json file in/home/pi directory  

3. Rename it to assistant--->assistant.json  

4. Using the one-line installer for installing Google Assistant and Snowboy dependencies
   Pi3 and Pi Zero Users use the corresponding scripts

	4.1 Make the installers Executable  
	```
	sudo chmod +x /home/pi/GassistPi/scripts/gassist-installer-pi3.sh
	sudo chmod +x /home/pi/GassistPi/scripts/gassist-installer-pi-zero.sh
	sudo chmod +x /home/pi/GassistPi/scripts/snowboy-deps-installer.sh  
  
	```
	4.2 Execute the installers (Don't be in a hurry and run them parallely, Run them one after the other)  
	```
	sudo  /home/pi/GassistPi/scripts/snowboy-deps-installer.sh
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi-zero.sh
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi3.sh  
	
	```

5. Copy the google assistant authentication link from terminal and authorize using your google account  

6. Copy the authorization code from browser onto the terminal and press enter    

7. Move into the environment and test the google assistant according to your board  

```
source env/bin/activate  
google-assistant-demo 
googlesamples-assistant-pushtotalk   
```  

8. After verying the working of assistant close and exit the terminal    

9. Copy the pushtotalk.py from "Voice-activation-pushtotalk" folder to the default pushtotalk folder and replace  



*************************************************  
**HEADLESS AUTOSTART ON BOOT SERVICE SETUP**  
*************************************************  
1. Make the service installer executable  

```
sudo chmod +x /home/pi/GassistPi/scripts/service-installer.sh 
```  

2. Run the service installer  

```
sudo /home/pi/GassistPi/scripts/service-installer.sh    
```  

3. Enable the services - Pi3 and Armv7 users enable all three services - Pi Zero users enable pushtotalk and snowboy services alone      
```
sudo systemctl enable gassistpi-ok-google.service  
sudo systemctl enable gassistpi-pushtotalk.service
sudo systemctl enable snowboy.service
```  

4. Start the service - Pi3 and Armv7 users start all three services - Pi Zero users start pushtotalk and snowboy services alone  

```
sudo systemctl start gassistpi-ok-google.service  
sudo systemctl start gassistpi-pushtotalk.service
sudo systemctl start snowboy.service   
```  
****************************************************
**Please Don't move or delete the trigger.txt file**  
****************************************************
**RESTART and ENJOY**  


************************************************
**VOICE CONTROL OF GPIOs and Pi Shutdown**
************************************************
The default GPIO and shutdown trigger word is "trigger" if you wish to change the trigger word, you can replace the 'trigger'in line 85 of the main.py code with your desired trigger word.

Similarly, you can define your own device names in line 35 under the variable name var.  

The number of GPIO pins declared in line 36 should match the number of devices.  

************************************************  
**FOR NEOPIXEL INDICAOR**
************************************************  
#Replace the main.py in src folder with the main.py from Neopixel Indicator Folder.  

#REBOOT  

#Change the Pin numbers in the given sketch according to your board and upload it.  

#Follow the circuit diagram given.  

************************************************  
**Now you have your Google Home Like Indicator**  
************************************************  
