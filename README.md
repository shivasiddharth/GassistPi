# GassistPi -- Google Assistant for all Raspberry Pi Boards  

**Pi Zero - forked and modified from warchildmd's repo (https://github.com/warchildmd/google-assistant-hotword-raspi)**  

# Features:  
**1.   Headless auto start on boot with multiple custom wakeword activation triggers.**    
**2.   Voice control of GPIOs without IFTTT, api.ai, Actions SDK.**   
**3.   Voice control of NodeMCU without IFTTT and MQTT.**  
**4.   Radio streaming.**  
**5.   Voice control of servo connected to RPi GPIO.**  
**6.   Safe shutdown RPi using voice command.**  
**7.   Stream Music from YouTube.**  
**8.   Indicator lights for assistant listening and speaking events.**  
**9.   Startup audio and audio feedback for wakeword detection.**   
**10.  Pushbutton service to stop Music or Radio playback.**   

# Features coming soon:
**1. Mute button.**  
**2. Blinkt! RGB indicator. (Neopixel is interfering with Pi Audio and I2S so cannot be used without arduino).**   

*******************************************************************************************************************************  
**Finally !! The project has been update to Python3. This means a better snowboy control and lower CPU utilization on Pi Zero Boards.**  **Users who installed GassistPi prior to 12th Nov 2017, please reformat the SD Card and re-install the Assistant to update the project to Python3.**  
*******************************************************************************************************************************

*******************************************************************************************************************************  
**CLI or Raspbian Lite does not support all features and Custom wakeword does not work with Google's AIY image. So please use the Standard Raspbian Desktop image- Link https://www.raspberrypi.org/downloads/raspbian/**  
*******************************************************************************************************************************

*************************************************
**FIRST STEP- CLONE the PROJECT on to Pi**   
*************************************************
1. Open the terminal and execute the following  

git clone https://github.com/shivasiddharth/GassistPi    


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
**The speaker-test command is used to initialize alsa, so please do not skip that.  
AIY-HAT and CUSTOM-HAT users, please reboot the Pi at places mentioned, else it will lead to audio and taskbar issues.          
(Run the commands till you get .bak notification in the terminal)**  

  3.1. USB DAC or USB Sound CARD users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
  sudo /home/pi/GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh 
  speaker-test  
  ```

  3.2. AIY-HAT users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
  sudo /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
  sudo reboot  
  sudo chmod +x /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
  sudo /home/pi/GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
  speaker-test  
  ```

  3.3. USB MIC AND HDMI users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
  sudo /home/pi/GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
  speaker-test  
  ```

  3.4. USB MIC AND AUDIO JACK users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
  sudo /home/pi/GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
  speaker-test  
  ```

  3.5. CUSTOM VOICE HAT users,  
  ```
  sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
  sudo /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
  sudo reboot    
  sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh  
  sudo /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh  
  speaker-test   
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
**CONTINUE after SETTING UP AUDIO**
**********************************************************************   

1. Download credentials--->.json file (refer to this doc for creating credentials https://developers.google.com/assistant/sdk/develop/python/config-dev-project-and-account)   

2. Place the .json file in/home/pi directory  

3. Rename it to assistant--->assistant.json  

4. Using the one-line installer for installing Google Assistant and Snowboy dependencies    
**Pi3 and Armv7 users use the "gassist-installer-pi3.sh" installer and Pi Zero, Pi A and Pi 1 B+ users use the "gassist-installer-pi-zero.sh" installer. Snowboy installer is common for both**  
	4.1 Make the installers Executable  
	```
	sudo chmod +x /home/pi/GassistPi/scripts/gassist-installer-pi3.sh
	sudo chmod +x /home/pi/GassistPi/scripts/gassist-installer-pi-zero.sh
	sudo chmod +x /home/pi/GassistPi/scripts/snowboy-deps-installer.sh  

	```
	4.2 Execute the installers **Pi3 and Armv7 users use the "gassist-installer-pi3.sh" installer and Pi Zero, Pi A and Pi 1 B+ users use the "gassist-installer-pi-zero.sh" installer. Snowboy installer is common for both**  
	**Don't be in a hurry and Don't run them parallely, Run them one after the other**
	```
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi3.sh  
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi-zero.sh
	sudo  /home/pi/GassistPi/scripts/snowboy-deps-installer.sh

	```

5. Copy the google assistant authentication link from terminal and authorize using your google account  

6. Copy the authorization code from browser onto the terminal and press enter    

7. Move into the environment and test the google assistant according to your board  

```
source env/bin/activate  
google-assistant-demo
googlesamples-assistant-pushtotalk   
```  

8. After verifying the working of assistant, close and exit the terminal    


*************************************************  
**HEADLESS AUTOSTART on BOOT SERVICE SETUP**  
*************************************************  
1. Make the service installer executable  

```
sudo chmod +x /home/pi/GassistPi/scripts/service-installer.sh
```  

2. Run the service installer  

```
sudo /home/pi/GassistPi/scripts/service-installer.sh    
```  

3. Enable the services - **Pi3 and Armv7 users, if you need custom wakeword functionality, then enable both the services, else enable just the "gassistpi-ok-ggogle.service" - Pi Zero, Pi A and Pi 1 B+ users, enable snowboy services alone**        
**To stop music playback using a pushbutton connected to GPIO 23 enable stopbutton.service**  
```
sudo systemctl enable gassistpi-ok-google.service  
sudo systemctl enable snowboy.service
sudo systemctl enable stopbutton.service  
```  

4. Start the service - **Pi3 and Armv7 users, if you need custom wakeword functionality, then start both the services, else start just the "gassistpi-ok-ggogle.service" - Pi Zero, Pi A and Pi 1 B+ users, start snowboy.service alone**    
**To stop music playback using a pushbutton connected to GPIO 23 start stopbutton.service**  
```
sudo systemctl start gassistpi-ok-google.service  
sudo systemctl start snowboy.service   
sudo systemctl start stopbutton.service  
```  

**RESTART and ENJOY**  

*******************************************************************
**INDICATORS for GOOGLE ASSISTANT'S LISTENING AND SPEAKING EVENTS**  
*******************************************************************
Connect LEDs with colours of your choice to GPIO05 for Listening and GPIO06 for Speaking Events.  

*******************************************************************
**PUSHBUTTON TO STOP MUSIC/RADIO PLAYBACK**  
*******************************************************************
Connect a pushbutton between GPIO23 and Ground. Using this pushbutton, now you can stop the music or radio playback.  


************************************************
**VOICE CONTROL of GPIOs, SERVO and Pi SHUTDOWN**
************************************************
The default GPIO and shutdown trigger word is **trigger**. It should be used for controlling the GPIOs, servo and for safe shutdown of Pi.

It has been intentionally included to prevent control actions due to false positive commands.  If you wish to change the trigger word, you can replace the '**trigger**'in the main.py and assistant.py code with your desired trigger word.

The default keyword for servo motor is **servo**. For example, the command **trigger servo 90** will rotate the servo by 90 degrees.   

If you wish to change the keyword, you can replace the 'servo' in the action.py script with your desired keyword for the motor.

For safe shutdown of the pi, command is: **trigger shutdown**  

You can define your own custom actions in the **actions.py** script.  
**THE ACTIONS SCRIPT OF THIS PROJECT IS DIFFERENT FROM AIY KIT's SCRIPT, COPY PASTING THE COMMANDS FROM AIY's ACTION SCRIPT WILL NOT WORK HERE. FOR A BETTER UNDERSTANDING OF THE ACTIONS FILE, FOLLOW THE FOLLOWING YOUTUBE VIDEO.**    

<a href="http://www.youtube.com/watch?feature=player_embedded&v=-MmxWWgceCg
" target="_blank"><img src="http://img.youtube.com/vi/-MmxWWgceCg/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>


************************************************
**VOICE CONTROL of NodeMCU**
************************************************
Download the Arduino IDE code for Nodemcu from here: https://github.com/shivasiddharth/iotwemos/blob/master/Google-Home-NodeMCU.ino  

Add the wifi credentials, make the desired changes and upload the Arduino code onto the NodeMCU and get the IP address from the serial monitor.  

Add the NodeMCU's IP address in the actions.py file.  

**FOR GUIDELINES ON MODIFYING THE ARDUINO CODE AND ACTIONS.PY FILE, FOLLOW THE FOLLOWING YOUTUBE VIDEO.**    

<a href="http://www.youtube.com/watch?feature=player_embedded&v=ae0iwJ62uaM
" target="_blank"><img src="http://img.youtube.com/vi/ae0iwJ62uaM/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>


************************************************
**MUSIC STREAMING from YOUTUBE**  
************************************************
Default keyword for playing music from YouTube is **Play**. For example, **Play I got you** command will fetch Bebe Rexha's I Got You from YouTube.  

Music streaming has been enabled for both OK-Google and Custom hotwords/wakewords.  

**Due to the Pi Zero's limitations, users are advised to not use the Music streaming feature. Music streaming will send the CPU usage of Pi Zero into the orbit.**  


************************************************
**RADIO STREAMING**  
************************************************
Default keyword for streaming radio is **tune into**. For example, **tune into Radio 2** command will open the corresponding radio stream listed in the actions.py file.    

Radio streaming has been enabled for both OK-Google and Custom hotwords/wakewords.

Useful links for obtaining radio streaming links:   
http://www.radiosure.com/stations/  

http://www.live-radio.net/worldwide.shtml  

http://worldradiomap.com/map/  

**Due to the Pi Zero's limitations, users are advised to not use the Radio streaming feature. Radio streaming will send the CPU usage of Pi Zero into next galaxy.**  


************************************************  
**FOR NEOPIXEL INDICAOR**
************************************************  
1. Change the Pin numbers in the given sketch according to your board and upload it.  

2. Follow the circuit diagram given.  

************************************************  
**LIST OF GPIOs USED**  
************************************************  
| GPIO Number (BCM) | Purpose                                        | 
|-------------------|------------------------------------------------|
| 25                | Assistant activity indicator for AIY Kits      | 
| 23                | Pushbutton to stop music/radio AIY and others  |    
| 05 and 06         | Google assistant listening and responding      |  
| 22                | Snowboy wakeword indicator                     |  
| 12,13,24          | Voice control of devices connected to GPIO     |  
| 27                | Voice control of servo                         |  

**Note: some HATS may use GPIOs 18, 19, 20, 21 for I2S audio please refer to the manufacturer's pinouts**          
