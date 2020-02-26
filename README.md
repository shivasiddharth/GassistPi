

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

6. After successful authentication, the Google Assistant Demo test will automatically start. At the start, the volume might be low, the assistant volume is independent of the Pi volume, so increase the volume by using "__Custom Wakeword__, Set volume to maximum" command.

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
**Pushbutton/Pi Zero/Pi B+ and other users**   
Open a terminal and execute the following:
```
/home/${USER}/env/bin/python -u /home/${USER}/GassistPi/src/pushbutton.py --project-id 'replace this with your project id'  --device-model-id 'replace this with the model id'

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
| __Custom Wakeword__, Shuffle my songs                | Shuffles all the songs added to the kodi library      |
| __Custom Wakeword__, Play songs from _Album name_                | Plays all the songs under the mentioned Album name  |    
| __Custom Wakeword__, Play songs by, _Artist name_         | Plays all the songs rendered by the mentioned artist      |  
| __Custom Wakeword__, Play _Song name_ song                | Plays the requested song, if it has been added to the library         |
| __Custom Wakeword__, Play _Movie name_ movie          | Plays the requested movie, if it has been added to the library     |  
| __Custom Wakeword__, From YouTube, Play _Youtube Video_         | Fetches the YouTube video and plays it on Kodi                  |
| __Custom Wakeword__, What is playing?                   | Tells you by voice as to what is currently playing |
| __Custom Wakeword__, Repeat this or Repeat one   | Repeats the current track playing|
| __Custom Wakeword__, Repeat all | Changes repeat mode to all |
| __Custom Wakeword__, Repeat off | Turns off Repeat|
| __Custom Wakeword__, Turn Shuffle On | Turns on shuffle mode|
| __Custom Wakeword__, Turn Shuffle Off | Turns off shuffle mode|
| __Custom Wakeword__, Play Next | Plays the next track|
| __Custom Wakeword__, Play Previous | Plays the previous track|
| __Custom Wakeword__, Scroll a bit forward | Fast forwards a movie/music by a small amount|
| __Custom Wakeword__, Scroll forward | Fast forwards a movie/track by a large margin |
| __Custom Wakeword__, Scroll a bit backward | Rewinds a movie/track by a small amount|
| __Custom Wakeword__, Scroll backward | Rewinds a movie/track by a large margin|
| __Custom Wakeword__, Set volume _Vol level number between 0 and 100_  | Sets the volume to the mentioned number |
| __Custom Wakeword__, Get volume | Tells you the current volume level by voice |
| __Custom Wakeword__, Toggle mute | Either mutes or unmutes, depending on mute status|
| __Custom Wakeword__, Pause | Pauses the current video/track |
| __Custom Wakeword__, Resume | Resumes playing the video/track|
| __Custom Wakeword__, Stop | Stops playing and closes the player |
| __Custom Wakeword__, goto _Home_ | Opens the appropriate menu or window mentioned |
| __Custom Wakeword__, goto  _Settings_  | Opens the settings menu or window |
| __Custom Wakeword__, goto _Videos_  | Opens the videos menu or window |
| __Custom Wakeword__, goto _Weather_  | Opens the weather menu or window |
| __Custom Wakeword__, goto _Music_  | Opens the music menu or window |
| __Custom Wakeword__, Move Up | Moves selection pointer up |
| __Custom Wakeword__, Move Down  | Moves selection pointer down |
| __Custom Wakeword__, Move Left  | Moves selection pointer left |
| __Custom Wakeword__, Move Right  | Moves selection pointer right |
| __Custom Wakeword__, Move Back | Goes back, equivalent to esc key |
| __Custom Wakeword__, Move Select | Makes a sletion, equivalent to enter key |
