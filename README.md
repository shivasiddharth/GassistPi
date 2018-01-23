

# GassistPi -- Google Assistant for all Raspberry Pi Boards  
*******************************************************************************************************************************
### **If you like the work, find it useful and if you would like to get me a :coffee: :smile:** [![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donate_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7GH3YDCHZ36QN)  

*******************************************************************************************************************************
## GassistPi updated with Google Play Music streaming and YouTube autoplay feature  

### Existing GassistPi users on the latest SDK can update their Pi using the given script to add the new feature. Due to Pi Zero's processing limitations, the feature has been added only for Pi 3 and Pi 2 users. Pi Zero users, need not update.
https://github.com/shivasiddharth/GassistPi/blob/update-script/GassistPi-09-Jan-2018-update.sh  

### New users, continue as instructed below in the README doc.
*******************************************************************************************************************************

# Features:  
**1.   Headless auto start on boot.**    
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
**14.  Streaming music from Google Play Music (It is computationally intensive so actions added only for Pi3 and Pi2).**    


*******************************************************************************************************************************  
**The Project has adopted the new Google Assistant SDK features released on 20th Dec 2017. Old installations will not work. So kindly Reformat your SD Card and start fresh**  
*******************************************************************************************************************************


*******************************************************************************************************************************  
**CLI or Raspbian Lite does not support all features and Custom wakeword does not work with Google's AIY image. So please use the Standard Raspbian Desktop image- Link https://www.raspberrypi.org/downloads/raspbian/**  
*******************************************************************************************************************************

*************************************************
## **FIRST STEP- CLONE the PROJECT on to Pi**   
*************************************************
1. Open the terminal and execute the following  

```
git clone https://github.com/shivasiddharth/GassistPi    
```

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

2. Place the .json file in/home/pi directory **DO NOT RENAME**  

3. Use the one-line installer for installing Google Assistant    
**Pi3 and Armv7 users use the "gassist-installer-pi3.sh" installer and Pi Zero, Pi A and Pi 1 B+ users use the "gassist-installer-pi-zero.sh" installer.**  
	4.1 Make the installers Executable  

	```
	sudo chmod +x /home/pi/GassistPi/scripts/gassist-installer-pi3.sh
	sudo chmod +x /home/pi/GassistPi/scripts/gassist-installer-pi-zero.sh

	```

	4.2 Execute the installers **Pi3 and Armv7 users use the "gassist-installer-pi3.sh" installer and Pi Zero, Pi A and Pi 1 B+ users use the "gassist-installer-pi-zero.sh" installer. When Prompted, enter your Google Cloud console Project-Id, A name for your Assistant and the Full Name of your credentials file, including the json extension.**  
	```
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi3.sh  
	sudo  /home/pi/GassistPi/scripts/gassist-installer-pi-zero.sh

	```

5. Copy the google assistant authentication link from terminal and authorize using your google account  

6. Copy the authorization code from browser onto the terminal and press enter    

7. After successful authentication, the Google Assistant Demo test will automatically start. At the start, the volume might be low, the assistant volume is independent of the Pi volume, so increase the volume by using "Volume Up" command.

8. After verifying the working of assistant, close and exit the terminal    


*************************************************  
## **HEADLESS AUTOSTART on BOOT SERVICE SETUP**  
*************************************************  
1. Open the service files in the /home/pi/GassistPi/systemd/ directory and add your project and model ids in the indicated places and save the file.

2. Make the service installer executable  

```
sudo chmod +x /home/pi/GassistPi/scripts/service-installer.sh
```  

3. Run the service installer  

```
sudo /home/pi/GassistPi/scripts/service-installer.sh    
```  

4. Enable the services - **Pi3 and Armv7 users, enable the "gassistpi-ok-ggogle.service" and Pi Zero, Pi A and Pi 1 B+ users, enable "gassistpi-push-button.service"**          
**To stop music playback using a pushbutton connected to GPIO 23 enable stopbutton.service**  
```
sudo systemctl enable gassistpi-ok-google.service  
sudo systemctl enable gassistpi-push-button.service
sudo systemctl enable stopbutton.service  
```  

5. Start the service - **Pi3 and Armv7 users, start the "gassistpi-ok-ggogle.service" and Pi Zero, Pi A and Pi 1 B+ users, start "gassistpi-push-button.service"**          
**To stop music playback using a pushbutton connected to GPIO 23 start stopbutton.service**   
```
sudo systemctl start gassistpi-ok-google.service  
sudo systemctl start gassistpi-push-button.service
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
The updated music streaming features autoplaying of YouTube suggestions. This makes use of the YouTube Data API v3.
### Adding YouTube API and Generating API Key
1. Go to the projects page on your Google Cloud Console-> https://console.cloud.google.com/project  
2. Select your project from the list.  
3. On the left top corner, click on the hamburger icon or three horizontal stacked lines.  
4. Move your mouse pointer over "API and services" and choose "credentials".
5. Click on create credentials and select API Key and choose close. Make a note of the created API Key and enter it in the actions.py script at the indicated location.  
6. "From the API and services" option, select library and in the search bar type youtube, select "YouTube Data API v3" API and click on "ENABLE".
7. In the API window, click on "All API Credentials" and in the drop down, make sure to have a tick (check mark) against the API Key that you just generated.


Music streaming has been enabled for both OK-Google and Custom hotwords/wakewords.  

Default keyword for playing music from **YouTube without autoplay** is **Stream**. For example, **Stream I got you** command will fetch Bebe Rexha's I Got You from YouTube.  

Default keyword for playing music from **YouTube with autoplay** is **Autoplay and Stream**. For example, **Autoplay and Stream I got you** command will play the requested I Got You and after the end of the track will autoplay susequent tracks. The number of autoplay tracks has been limited to a maximum of 10. this can be changed the under the YouTube_Autoplay function in the actions.py script.   

**Due to the Pi Zero's limitations, users are advised to not use the Music streaming feature. Music streaming will send the CPU usage of Pi Zero into the orbit.**  

************************************************
## **MUSIC STREAMING from Google Music**  
************************************************
The music streaming from Google Music uses [Gmusicapi](https://unofficial-google-music-api.readthedocs.io/en/latest/).

Enter your Google userid and password in the gmusic.py file in the line **"logged_in = api.login('YOUR_GMAIL_ID', 'YOUR_GMAIL_PASSWORD', Mobileclient.FROM_MAC_ADDRESS)"**. If you are using a two-step authentication or two-factor authentication, generate and use an app specific password.

### Getting app specific password:
Refer to this page on google help - https://support.google.com/accounts/answer/185833?hl=en

### What you can do:
Play all your songs in loop using the syntax: **"Hey Google, Play all the songs from Google Music"**

Play songs added to the user created playlist (does not include: most played playlist, thumsup playlist, etc) using the syntax: **"Hey Google, Play songs from the first playlist in Google Music"**
Playlists are sorted by date created, if you have multiple playlists, use a similar syntax replacing first with second, third etc. Also you need to make suitable changes in the main.py (It has been commented in the script to help)

Play songs by a particular artist using the syntax: **"Hey Google, Play songs by artist YOUR_ARTIST_NAME from Google Music"**

Play songs from particular album using the syntax: **"Hey Google, Play songs from album YOUR_ALBUM_NAME from Google Music"**

### What you cannot do at the moment: (some features may be added later):
Change tracks
Shuffle tracks
Repeat tracks

**Due to the Pi Zero's limitations, and computationally intensive nature of the Google Music streaming feature, this action has not been enabled for Pi Zero.**  


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
| 22                | Pushbutton trigger for gRPC API. Connect a pushbutton between GPIO 22 and GRND for manually triggering                     |  
| 12,13,24          | Voice control of devices connected to GPIO     |  
| 27                | Voice control of servo                         |  

**Note: some HATS may use GPIOs 18, 19, 20, 21 for I2S audio please refer to the manufacturer's pinouts**          
