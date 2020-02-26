

# Voice control OSMC with Goolge Assistant Built-in    
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
git clone https://github.com/shivasiddharth/GassistPi -b OSMC
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
The speaker-test command is used to initialize alsa, so please do not skip that.**  

    3.1. USB DAC or USB Sound CARD users,  
```
sudo chmod +x ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
sudo ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh
speaker-test  
```    

    3.2. USB MIC AND HDMI users,  
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

**Ok-Google Hotword/Pi3/Pi2/Armv7 users**   
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

************************************************  
### **KODI INTEGRATION**  
************************************************  
### Enabling Kodi control    
In the config.yaml, under kodi, change control option from **'Disabled'** to **'Enabled'**.  

### Adding YouTube API and Generating API Key
The Kodi integration uses YouTube Data API v3  for getting video links. First step is to add the API to the project and create an API KEY.
1. Go to the projects page on your Google Cloud Console-> https://console.cloud.google.com/project  
2. Select your project from the list.  
3. On the left top corner, click on the hamburger icon or three horizontal stacked lines.  
4. Move your mouse pointer over "API and services" and choose "credentials".
5. Click on create credentials and select API Key and choose close. Make a note of the created API Key and enter it in the config.yaml at the indicated location.  
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
| Hey Google, Scroll a bit backward on kodi| Rewinds a movie/track by a small amount|
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
