Google Has Just Released an Update to Make the Pi Detectable on the Home App, This project Needs to be modified accordingly, so this project will not be usable for time being. For more info please read through this https://developers.googleblog.com/2017/12/the-google-assistant-sdk-new-languages.html Once its ready, You can see it in the git here.


# GassistPi -- Google Assistant for all Raspberry Pi Boards  

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
**11.  Parcel tracking using Aftership API.**  
**12.  RSS Feed streaming.**  
**13.  Control of Kodi or Kodi Integration**.    

*******************************************************************************************************************************  
**Finally !! The project has been update to Python3. This means a better snowboy control and lower CPU utilization on Pi Zero Boards.**  **Users who installed GassistPi prior to 12th Nov 2017, please reformat the SD Card and re-install the Assistant to update the project to Python3.**  
*******************************************************************************************************************************

*******************************************************************************************************************************
**Existing Python3 GassistPi users, update the project using the script: https://github.com/shivasiddharth/GassistPi/blob/update-script/GassistPi-19-Dec-2017-update.sh**  
**New users, folow the instructions in this document.**  
*******************************************************************************************************************************


*******************************************************************************************************************************  
**CLI or Raspbian Lite does not support all features and Custom wakeword does not work with Google's AIY image. So please use the Standard Raspbian Desktop image- Link https://www.raspberrypi.org/downloads/raspbian/**  
*******************************************************************************************************************************

*************************************************
## **FIRST STEP- CLONE the PROJECT on to Pi**   
*************************************************
1. Open the terminal and execute the following  

git clone https://github.com/shivasiddharth/GassistPi    


*************************************************  
## **INSTALL AUDIO CONFIG FILES**
*************************************************  
1. Update OS and Kernel    

```
sudo apt-get update  
sudo apt-get install raspberrypi-kernel  
```

2. Restart Pi  

3. Choose the audio configuration according to your setup.   
**The speaker-test command is used to initialize alsa, so please do not skip that.  
AIY-HAT and CUSTOM-HAT users, please reboot the Pi at places mentioned, else it will lead to audio and taskbar issues.**  

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
  sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh  
  sudo /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh 
  sudo reboot 
  sudo chmod +x /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
  sudo /home/pi/GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
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
## **CONTINUE after SETTING UP AUDIO**
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
	sudo  /home/pi/GassistPi/scripts/snowboy-deps-installer.sh
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi3.sh  
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi-zero.sh
	
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
## **HEADLESS AUTOSTART on BOOT SERVICE SETUP**  
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
## **INDICATORS for GOOGLE ASSISTANT'S LISTENING AND SPEAKING EVENTS**  
*******************************************************************
Connect LEDs with colours of your choice to GPIO05 for Listening and GPIO06 for Speaking Events.  

*******************************************************************
## **PUSHBUTTON TO STOP MUSIC/RADIO PLAYBACK**  
*******************************************************************
Connect a pushbutton between GPIO23 and Ground. Using this pushbutton, now you can stop the music or radio playback.  


************************************************
## **VOICE CONTROL of GPIOs, SERVO and Pi SHUTDOWN**
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
## **VOICE CONTROL of NodeMCU**
************************************************
Download the Arduino IDE code for Nodemcu from here: https://github.com/shivasiddharth/iotwemos/blob/master/Google-Home-NodeMCU.ino  

Add the wifi credentials, make the desired changes and upload the Arduino code onto the NodeMCU and get the IP address from the serial monitor.  

Add the NodeMCU's IP address in the actions.py file.  

**FOR GUIDELINES ON MODIFYING THE ARDUINO CODE AND ACTIONS.PY FILE, FOLLOW THE FOLLOWING YOUTUBE VIDEO.**    

<a href="http://www.youtube.com/watch?feature=player_embedded&v=ae0iwJ62uaM
" target="_blank"><img src="http://img.youtube.com/vi/ae0iwJ62uaM/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>


************************************************
## **MUSIC STREAMING from YOUTUBE**  
************************************************
Default keyword for playing music from YouTube is **Play**. For example, **Play I got you** command will fetch Bebe Rexha's I Got You from YouTube.  

Music streaming has been enabled for both OK-Google and Custom hotwords/wakewords.  

**Due to the Pi Zero's limitations, users are advised to not use the Music streaming feature. Music streaming will send the CPU usage of Pi Zero into the orbit.**  


************************************************
## **RADIO STREAMING**  
************************************************
Default keyword for streaming radio is **tune into**. For example, **tune into Radio 2** command will open the corresponding radio stream listed in the actions.py file.    

Radio streaming has been enabled for both OK-Google and Custom hotwords/wakewords.

Useful links for obtaining radio streaming links:   
http://www.radiosure.com/stations/  

http://www.live-radio.net/worldwide.shtml  

http://worldradiomap.com/map/  

**Due to the Pi Zero's limitations, users are advised to not use the Radio streaming feature. Radio streaming will send the CPU usage of Pi Zero into next galaxy.**  

***********************************************  
## **FOR PARCEL TRACKING**  
***********************************************  
The default keyword for tracking parcel is **parcel**. For example, you can say **where is my parcel** or **track my parcel**.  

Regsiter for a free account with Aftership at https://www.aftership.com gnereate an API number and add parcels to the tracking list.
The generated API number should be added to the actions.py script at the indicated location. For a better understanding follow the attached youtube video.

<a href="http://www.youtube.com/watch?feature=player_embedded&v=WOyYL46s-q0
" target="_blank"><img src="http://img.youtube.com/vi/WOyYL46s-q0/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>

************************************************  
## **FOR RSS FEEDS**  
************************************************  
Default keywords for playing RSS feeds is **feed** or **news** or **quote**. Example usage, **top tech news** will play the top technology news, **top world news** will play top news related to different countires, **top sports news** will play the top sports related news and **quote of the day** will give some quotes.

Do not mix the commands with **Play** as that has been associated with music streaming from YouTube.  

**numfeeds** variable within the feed function in actions.py file is the feed limit. Certain RSS feeds can have upto 60 items and **numfeeds** variable limits the number of items to stream. The default value has been set to 10, which if you want can change.  


************************************************  
## **KODI INTEGRATION**  
************************************************  
### Adding YouTube API and Generating API Key
The Kodi integration uses YouTube Data API v3  for getting video links. First step is to add the API to the project and create an API KEY.
1. Go to the projects page on your Google Cloud Console-> https://console.cloud.google.com/project  
2. Select your project from the list.  
3. On the left top corner, click on the hamburger icon or three horizontal stacked lines.  
4. Move your mouse pointer over "API and services" and choose "credentials".
5. Click on create credentials and select API Key and choose close. Make a note of the created API Key and enter it in the actions.py script at the indicated location.  
6. "From the API and services" option, select library and in the search bar type youtube, select "YouTube Data API v3" API and click on "ENABLE".
7. In the API window, click on "All API Credentials" and in the drop down, make sure to have a tick (check mark) against the API Key that you just generated.  

### Enabling HTTP Control on Kodi
The webserver is disabled by default and has to be manually enabled by the user. 
1. This can be done in Settings → Services → Control → Allow remote control via HTTP.   
2. Set the port number to 8080, username to kodi and password to kodi  
(username and password should be in lowercase).

### Adding YouTube plugin on Kodi
For Kodi to play the YouTube video, you need to add and enable the YouTube Plugin on Kodi.  

### Command Sytanxes for Kodi Control  
**Note that "on Kodi" should be used in all the commands. If you want to use it exclusively, for Kodi Control, replace the given main.py and assistants.py file with the ones provieded in the extras/Kodi Intergration/ folder. In that, "on kodi" has been programatically added and other functions have been disabled,even genral queries like time and weather will not work. It is to be used only for the following Kodi commands.**  

| Command Syntax    | What it does                                        | 
|-------------------|------------------------------------------------|
| Hey Google, Shuffle my songs on kodi               | Shuffles all the songs added to the kodi library      | 
| Hey Google, Play songs from _Album name_ on kodi               | Plays all the songs under the mentioned Album name  |    
| Hey Google, Play songs by, _Artist name_ on kodi        | Plays all the songs rendered by the mentioned artist      |  
| Hey Google, Play _Song name_ song on kodi               | Plays the requested song, if it has been added to the library         | 
| Hey Google, Play _Movie name_ movie on kodi         | Plays the requested movie, if it has been added to the library     |  
| Hey Google, From YouTube, Play _Youtube Video_ on kodi        | Fetches the YouTube video and plays it on Kodi                  | 
| Hey Google, What is playing? on kodi                  | Tells you by voice as to what is currently playing |
| Hey Google, Repeat this or Repeat one on kodi  | Repeats the current track playing|
| Hey Google, Repeat all on kodi| Changes repeat mode to all |
| Hey Google, Repeat off on kodi| Turns off Repeat|
| Hey Google, Turn Shuffle On on kodi| Turns on shuffle mode|
| Hey Google, Turn Shuffle Off on kodi| Turns off shuffle mode|
| Hey Google, Play Next on kodi| Plays the next track|
| Hey Google, Play Previous on kodi| Plays the previous track|
| Hey Google, Scroll a bit forward on kodi| Fast forwards a movie/music by a small amount|
| Hey Google, Scroll forward on kodi| Fast forwards a movie/track by a large margin |
| Hey Google, Scroll a biy backward on kodi| | Rewinds a movie/track by a small amount|
| Hey Google, Scroll backward on kodi| Rewinds a movie/track by a large margin|
| Hey Google, Set volume _Vol level number between 0 and 100_ on kodi | Sets the volume to the mentioned number |
| Hey Google, Get volume on kodi| Tells you the current volume level by voice |
| Hey Google, Toggle mute on kodi| Either mutes or unmutes, depending on mute status|
| Hey Google, Pause on kodi| Pauses the current video/track |
| Hey Google, Resume on kodi| Resumes playing the video/track|
| Hey Google, Stop on kodi| Stops playing and closes the player |
| Hey Goolge, goto _Home_ on kodi| Opens the appropriate menu or window mentioned |
| Hey Goolge, goto  _Settings_ on kodi | Opens the settings menu or window |
| Hey Goolge, goto _Videos_ on kodi | Opens the videos menu or window |
| Hey Goolge, goto _Weather_ on kodi | Opens the weather menu or window |
| Hey Google, goto _Music_ on kodi | Opens the music menu or window |
| Hey Google, Move Up on kodi| Moves selection pointer up |
| Hey Google, Move Down on kodi | Moves selection pointer down |
| Hey Google, Move Left on kodi | Moves selection pointer left |
| Hey Google, Move Right on kodi | Moves selection pointer right |
| Hey Google, Move Back on kodi| Goes back, equivalent to esc key | 
| Hey Google, Move Select on kodi| Makes a sletion, equivalent to enter key | 


************************************************  
## **FOR NEOPIXEL INDICATOR**
************************************************  
1. Change the Pin numbers in the given sketch according to your board and upload it.  

2. Follow the circuit diagram given.  

************************************************  
## **LIST OF GPIOs USED**  
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
