

# GassistPi -- Google Assistant for Single Board Computers    
*******************************************************************************************************************************
### **If you like the work, find it useful and if you would like to get me a :coffee: :smile:** [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7GH3YDCHZ36QN)

### **Community: For Non-Issue Help and Interaction** [![Join the chat at https://gitter.im/publiclab/publiclab](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/GassistPi/Lobby/)
*******************************************************************************************************************************
## 26-Nov-2018 Update:
**GassistPi has been ported to work with Pi as well as other SBCs running Armbian Stretch.**          
*******************************************************************************************************************************

# Features (All features are applicable to all boards, unless and otherwise mentioned):  
**1.   Headless auto start on boot.**    
**2.   Voice control of GPIOs without IFTTT, api.ai, Actions SDK (Only for Raspberry Pi Boards).**   
**3.   Voice control of NodeMCU without IFTTT and MQTT.**  
**4.   Radio streaming.**  
**5.   Voice control of servo connected to RPi GPIO (Only for Raspberry Pi Boards).**    
**6.   Safe shutdown RPi using voice command.**  
**7.   Stream Music from YouTube.**  
**8.   Indicator lights for assistant listening and speaking events.**  
**9.   Startup audio and audio feedback for wakeword detection.**   
**10.  Pushbutton service to stop Music or Radio playback.**   
**11.  Parcel tracking using Aftership API.**  
**12.  RSS Feed streaming.**  
**13.  Control of Kodi or Kodi Integration.**    
**14.  Streaming music from Google Play Music.**  
**15.  Casting of YouTube Videos to Chromecast and Chromecast media control by voice.**  
**16.  Voice control of Radio/YouTube/Google Music volume levels.**         
**17.  Control Sonoff Tasmota Devices/Emulated Wemo.**  
**18.  Track [Kickstarter](https://www.kickstarter.com) campaigns.**  
**19.  Emulated Philips Hue HUB service and control of Emulated Hue Lights.**  
**20.  Search recipes and get push message of ingredients and link to recipe.**    
**21.  Remote control of Magic Mirror.**  
**22.  Sending voice messages from the phone to the raspberry.**  
**23.  Play your Spotify playlist.**  
**24.  Custom wakeword activation for all Pi boards.**      
**25.  Mute microphones to prevent listening to Ok-Google hotword (Only Raspberry Pi Boards).**  
**26.  Create custom conversations.**  
**27.  Control of lights added to Domoticz.**  
**28.  Stream music from Gaana.com.**  
**29.  Stream your playlist from Deezer.**    
**30.  Custom actions in French, Italian, German, Dutch and Spanish.**    

*******************************************************************************************************************************  
### Only OSes suported are:
- Armbian Stretch    
- Raspbian Stretch   

**Raspberry Pi users please use the latest Raspbian Desktop/Lite image- [Link](https://www.raspberrypi.org/downloads/raspbian/). Other board users please use the lastest Armbian image- [Link](https://www.armbian.com/download/)**  
*******************************************************************************************************************************

### NOTE: "${USER}" will automatically take your username. No need to change that. Just copy pasting the following commands on terminal will work.  

*************************************************
## **FIRST STEP- CLONE the PROJECT on to Pi**   
*************************************************
1. Open the terminal and execute the following  

```
sudo apt-get install git  
git clone https://github.com/shivasiddharth/GassistPi    
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

1. Follow the instructions [here](https://developers.google.com/assistant/sdk/guides/library/python/embed/config-dev-project-and-account) to Configure a Developer Project and Account Settings. Then follow this [guide](https://developers.google.com/assistant/sdk/guides/library/python/embed/register-device) to register the device and obtain the credentials.json file. Refer to the video below for step by step guidelines.  

<a href="http://www.youtube.com/watch?feature=player_embedded&v=dMNtmp8z52M
" target="_blank"><img src="http://img.youtube.com/vi/dMNtmp8z52M/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>


2. Place the credentials.json file in/home/${USER}/ directory **DO NOT RENAME**  

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
**Pushbutton/Pi Zero/Pi B+ and other users**   
Open a terminal and execute the following:
```
/home/${USER}/env/bin/python -u /home/${USER}/GassistPi/src/pushbutton.py --project-id 'replace this with your project id'  --device-model-id 'replace this with the model id'

```
Insert your Project Id and Model Id in quotes in the mentioned places

*******************************************************************
## **USING THE CUSTOMIZATIONS**  
*******************************************************************
### **CUSTOM ACTIONS IN Non-English LANGUAGES**    
************************************************
Languages supported: French, Italian, Spanish, Dutch and German.  

In the **config.yaml** file, under the **Languages and Choice** option set your desired language.   

Use the Translated versions of the English syntaxes given for all the custom actions.  

************************************************
### **MUSIC STREAMING FROM DEEZER**  
************************************************
**NOTE: As a roundabout approach, I have programmed the assistant to get the playlist details using Deezer API and then fetch those tracks from YouTube.**   
This feature uses a YouTube Data API v3.  
### Adding YouTube Data API and Generating API Key  
1. Go to the projects page on your Google Cloud Console-> https://console.cloud.google.com/project  
2. Select your project from the list.  
3. On the left top corner, click on the hamburger icon or three horizontal stacked lines.  
4. Move your mouse pointer over "API and services" and choose "credentials".
5. Click on create credentials and select API Key and choose close. Make a note of the created API Key and enter it in the **config.yaml** script at the indicated location.  
6. "From the API and services" option, select library and in the search bar type **youtube**, select "YouTube Data API v3" API and click on "ENABLE".  
7. In the API window, click on "All API Credentials" and in the drop down, make sure to have a tick (check mark) against the API Key that you just generated.  
8. Add your Deezer user number in the **config.yaml** under the "Deezer" and "User_id".  

**Note: The same API key can be used for Kickstarter, YouTube and Gaana feature.**  

Syntax:  
1. To play the playlists added to your Deezer account:    
Hey Google, Play playlist _playlist-number_ from Deezer   
Example: Hey Google, Play playlist 1 from Deezer   

************************************************
### **MUSIC STREAMING FROM GAANA.COM**  
************************************************
**NOTE: As a roundabout approach, I have programmed the assistant to get the playlist details using web requests and then fetch those tracks from YouTube.**   
This feature uses a custom search engine as well as YouTube Data API v3.  
### Adding Google Custom Search Engine API, YouTube Data API and Generating API Key  
1. Go to the projects page on your Google Cloud Console-> https://console.cloud.google.com/project  
2. Select your project from the list.  
3. On the left top corner, click on the hamburger icon or three horizontal stacked lines.  
4. Move your mouse pointer over "API and services" and choose "credentials".
5. Click on create credentials and select API Key and choose close. Make a note of the created API Key and enter it in the **config.yaml** script at the indicated location.  
6. "From the API and services" option, select library and in the search bar type **search**, select "Custom Search API" and click on "ENABLE".
7. "From the API and services" option, select library and in the search bar type **youtube**, select "YouTube Data API v3" API and click on "ENABLE".  
8. In the API window, click on "All API Credentials" and in the drop down, make sure to have a tick (check mark) against the API Key that you just generated.  

**Note: The same API key can be used for Kickstarter and YouTube feature.**  

Syntaxes:  
**Note - It is necessary to Say the full "Gaana.com", otherwise the assistant will pick it up as Ghana (a country).**    
1. To play the playlists added in config.yaml file:  
Hey Google, Play playlist _playlist-number_ from Gaana.com   
Example: Hey Google, Play playlist 1 from Gaana.com   

2. To play other playlists:  
Hey Google, Play _user-playlist-query_ from Gaana.com

************************************************
### **DOMOTICZ CONTROL**  
************************************************
As of today, you can control lights and switches only, more controls will be added in the future.  
1. If you want to control devices with Domoticz, in the config.yaml file under **"Domoticz:"** change **"Domoticz_Control:"** from **"Disabled"** to **"Enabled"**.  
2. List the device names and the ids that you want to control in the config.yaml file. The names should be the same as the ones in the domoticz server.    
3. Syntaxes:  
To On/Off/Toggle (The light name should be the same as the Hardware name in Domoticz):  
Hey Google, Turn On/Turn Off/Toggle  _Name of your light_ .  
To Change Brightness (between 0 and 100):  
Hey Google, Set  _Name of your light_ brightness to _desired value_ .    
To Change Colour (refer the list of available colors given below):
Hey Google, Set  _Name of your light_ color to _desired color_ .  
Hey Google, Change  _Name of your light_ to _desired color_ .      

************************************************
### **CUSTOM CONVERSATIONS**  
************************************************
1. Customize the assistant's reply to a specific question.  
2. Add the list of questions and answers in config.yaml under the **Conversation:** option.  
3. **There must be only one question, but corresponding answers can be as many.**  
4. Sample questions and answers has been provided, please follow the same pattern.  

************************************************
### **CUSTOM WAKEWORD ACTIVATION**  
************************************************
1. You can choose to either Enable or Disable the custom wakeword activation in the config.yaml file.  
2. In the config.yaml file, under Wakewords, change the **"Custom_Wakeword"** to 'Enabled' if you want to use the custom wakeword or set it to 'Disabled' if you dont want to use the custom wakeword option.  
3. For changes to take effect, you need to restart the assistant. Changing status while an instance of assistant is already running will not cause any change.  
4. Create your custom snowboy model [here](https://snowboy.kitt.ai). Add the models to **/GassistPi/src/resources**  directory.
5. Change the paths to the models in the config.yaml file.  
6. To disable the default **"Ok Google"** hotword, set the **Ok_Google option to "Disabled"**.  
7. Users using pushbutton.py or Pi Zero users have an option between using custom wakeword and GPIO trigerring. If custom wakeword is enabled, then GPIO trigger will not work. To enable GPIO triggering, set custom wakeword to 'Disabled'.    

************************************************
### **PLAYING SPOTIFY PLAYLIST**  
************************************************
**NOTE: Spotify API currently only supports playback in a web browser, but DRM content is being blocked in the Raspberry Pi. As a roundabout approach, I have programmed the assistant to get the playlist details using Spotipy API and then fetch those tracks from YouTube. This custom program has a better accuracy than spotify playlist playback using mpsyt.**   

1. Click [here](https://developer.spotify.com/dashboard/login) and register for a spotify developer account, if you already don't have one.  
2. In the developer's dashboard, choose "**CREATE A CLIENT ID**". In the pop-up window provide the requested details.  
3. Click on the new app created and copy the CLIENT ID and CLIENT SECRET. Paste it in the config.yaml file in the indicated space.
4. Access spotify:[here]( https://www.spotify.com/account/overview/) and copy the username to be entered in config.yaml

**Syntax: Hey Google, Play _Your Spotify Playlist Name_ from Spotify**


************************************************
### **TRACKING KICKSTARTER CAMPAIGNS**  
************************************************
A custom Google search engine for [Kickstarter](https://www.kickstarter.com) has been used. This requires an API to be added to your existing project.  
### Adding Google Custom Search Engine API and Generating API Key
1. Go to the projects page on your Google Cloud Console-> https://console.cloud.google.com/project  
2. Select your project from the list.  
3. On the left top corner, click on the hamburger icon or three horizontal stacked lines.  
4. Move your mouse pointer over "API and services" and choose "credentials".
5. Click on create credentials and select API Key and choose close. Make a note of the created API Key and enter it in the **config.yaml** script at the indicated location.  
6. "From the API and services" option, select library and in the search bar type **search**, select "Custom Search API" and click on "ENABLE".
7. In the API window, click on "All API Credentials" and in the drop down, make sure to have a tick (check mark) against the API Key that you just generated.

**Note: The same API key can be used for YouTube and Gaana, but YouTube Data v3 API must be added to the project in the cloud console.**  

**Syntax: Hey Google, (What is the status of) or (Track) _Your Desired Campaign Name_ Kickstarter campaign**  


************************************************
### **EMULATED PHILIPS HUE SEVICE AND CONTROL**  
************************************************
Credits for the [Emulated Hue](https://github.com/mariusmotea/diyHue) to [Marius Motea](https://github.com/mariusmotea).  

Follow the guidelines given in the diyHue's Wiki to setup the Emulated Hue Service.  

Download sketches for your NodeMCU/Wemos/ESP Devices from [here](https://github.com/mariusmotea/diyHue/tree/master/Lights)

After making suitable modifications and uploading the sketches to your device, open the device's webgui by entering the ip address in a browser. In that change the "Startup" value from "Last State" to "Off" as shown below.  

<img src="https://drive.google.com/uc?id=1_5QSs7Bm9TeXgazmTdvwiL34yNXot4AV"
width="300" height="600" border="1" /> | <img src="https://drive.google.com/uc?id=14mPEptFRBwwv1AmsH3qORCCez63uU1LM"
width="300" height="600" border="1" />

Depending upon your device, download the Philips Hue App for either of the platforms from the following links.  

<a href="https://itunes.apple.com/ie/app/philips-hue/id1055281310?mt=8
" target="_blank"><img src="https://drive.google.com/uc?id=1k6IjneSQ0P6wRaHt8rjfNBiC7Y3iVGlV"
alt="Apple App Store Philips Hue App" width="200" height="80" border="1" /></a>                  <a href="https://play.google.com/store/apps/details?id=com.philips.lighting.hue2&hl=en
" target="_blank"><img src="https://drive.google.com/uc?id=1Qh6tdhcxZTRPOvkL1lptdbvdTiHRM7Vq"
alt="Google Play Philips Hue App" width="200" height="80" border="1" /></a>

#### **To pair the diyHue to the app:**    
To pair a new device to diyHue, first head to http://{IP_ADDRESS}/hue/linkbutton.   
The default username is **Hue** and password is **Hue**.   
At this point you should open the Hue app on your phone and start searching for hubs.   
To speed this up you can click the Help button and then enter the IP address of your diyHue device.   
Once the bridge has been detected, click the green Set up button. At this point, the app will prompt you to press the link button on your Hue bridge.   
To do so, click the Activate button on the web page you loaded at the start.
The Hue app should now prompt you through the rest of the setup. For specific details on how to setup specific lights, browse the lights section in the navigation bar to the right.     

**Command Syntax:**    
**To turn lights on/off :** "Hey Google, Turn _Hue-Light-Name_ On/Off"    
**To change light colour:** "Hey Google, Change _Hue-Light-Name_ colour to _Required-Colour_"  (List of available colours is given at the end of readme doc)  
**To change brightness  :** "Hey Google, Change _Hue-Light-Name_ brightness to _Required-Brightness-Level_"   


*******************************************************************
### **PUSHING MESSAGES/INFO FROM ASSISTANT ON Pi TO ANDROID DEVICE**  
*******************************************************************
For pushing messages/info, the GassistPi uses pushbullet python package. To use this feature:  
1. Download and install pushbullet app on your tablet/mobile device.  
2. Visit www.pushbullet.com register for new account or sign in with your existing account.  
3. Choose Settings-->Account and then choose "Create access token".  
4. Copy this token and paste in the actions.py script under the pushmessage function.  


*******************************************************************
### **GETTING RECIPE DETAILS USING ASSISTANT**  
*******************************************************************
GassistPi uses [Edamam](www.edamam.com) for getting recipe details/info. To use this feature:  
1. Click [here](https://developer.edamam.com/edamam-recipe-api) to visit the developers' porta for Edamam.  
2. Signup as a developer/login with your existing account.  
3. In the Menubar at the top, Click on Dashboard-->Applications-->Create a new applicatiuon-->Recipe Search API and then create a new application.  
4. Copy the application id and application key and paste it in the actions.py script under the getrecipe function.  
**(Note: While copying the application key, do not copy the "—")  

Command Syntax:  
"Hey Google, Get ingredients for _Required-Item_"  


*******************************************************************
### **CONTROLLING MAGIC MIRROR BY VOICE**  
*******************************************************************
You can control either Magic Mirror running on another Pi or Magic Mirror running on the same pi as GassistPi.  
As a prerequisite, you should have the remote control module installed in the Pi running Magic Mirror.  
Enter the Ip address of Pi running Magic Mirror in the **config.yaml** against the variable **"mmmip"** declared.   

Command Syntax:  
**To show/hide weather module             :**  "Hey Google, Show/Hide Weather on Magic Mirror"  
**To turn magic mirror display on/off     :**  "Hey Google, Turn Magic Mirror display on/off"  
**To power off/reboot/restart Magic Mirror:**  "Hey Google, Power off/Reboot/Restart Magic Mirror"  


*******************************************************************
### **INDICATORS FOR GOOGLE ASSISTANT'S LISTENING AND SPEAKING EVENTS**  
*******************************************************************
Connect LEDs with colours of your choice to GPIO05 for Listening and GPIO06 for Speaking Events.  

*******************************************************************
### **PUSHBUTTON TO STOP MUSIC/RADIO PLAYBACK AND MUTE MICROPHONE**  
*******************************************************************
Connect a pushbutton between GPIO23 and Ground. Single press mutes microphone and double press stops music streaming.  


************************************************
### **VOICE CONTROL OF GPIOs, SERVO and Pi SHUTDOWN**
************************************************
The default GPIO and shutdown trigger word is **trigger**. It should be used for controlling the GPIOs, servo and for safe shutdown of Pi.

It has been intentionally included to prevent control actions due to false positive commands.  If you wish to change the trigger word, you can replace the '**trigger**'in the main.py code with your desired trigger word.

The default keyword for servo motor is **servo**. For example, the command **trigger servo 90** will rotate the servo by 90 degrees.   

If you wish to change the keyword, you can replace the 'servo' in the action.py script with your desired keyword for the motor.

For safe shutdown of the pi, command is: **trigger shutdown**  

You can define your own custom actions in the **actions.py** script.  
**THE ACTIONS SCRIPT OF THIS PROJECT IS DIFFERENT FROM AIY KIT's SCRIPT, COPY PASTING THE COMMANDS FROM AIY's ACTION SCRIPT WILL NOT WORK HERE. FOR A BETTER UNDERSTANDING OF THE ACTIONS FILE, FOLLOW THE FOLLOWING YOUTUBE VIDEO.**    

<a href="http://www.youtube.com/watch?feature=player_embedded&v=-MmxWWgceCg
" target="_blank"><img src="http://img.youtube.com/vi/-MmxWWgceCg/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>


************************************************
### **VOICE CONTROL OF NodeMCU**
************************************************
There are two ways to control NodeMCU:  
1. Control of NodeMCU running a webserver.  
2. Control of NodeMCU running Sonoff-Tasmota Firmware.  

### **Controlling NodeMCU running webserver**   
Download the Arduino IDE code for Nodemcu from here: https://github.com/shivasiddharth/iotwemos/blob/master/Google-Home-NodeMCU.ino  

Add the wifi credentials, make the desired changes and upload the Arduino code onto the NodeMCU and get the IP address from the serial monitor.  

Add the NodeMCU's IP address in the **config.yaml**.  

**Syntax: "Hey Google, Trigger Turn _Devicename_ On/Off"**    

**FOR GUIDELINES ON MODIFYING THE ARDUINO CODE AND ACTIONS.PY FILE, FOLLOW THE FOLLOWING YOUTUBE VIDEO.**    

<a href="http://www.youtube.com/watch?feature=player_embedded&v=ae0iwJ62uaM
" target="_blank"><img src="http://img.youtube.com/vi/ae0iwJ62uaM/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>

### **Controlling NodeMCU running Sonoff-Tasmota firmware**  
Download the Tasmota firmware from this [link](https://mega.nz/#!Dwx0lDYL!CK_QYoR9GvBhqdEmVs98ac45TjTjPIQyeaezYT4jfE0)

Follow the instructions in this video to upload the firmware properly.  

<a href="http://www.youtube.com/watch?feature=player_embedded&v=MzcAS-K_TRU
" target="_blank"><img src="http://img.youtube.com/vi/MzcAS-K_TRU/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>  

Pi3 and Pi Zero users, assign the device names and device ip addresses in the **config.yaml** in the marked locations.  

**Syntax: "Hey Google, Turn _Devicename_ On/Off"**  

Advantage of using Sonoff-Tasmota over webserver is that, with Sonoff-Tasmota you can emulate a Wemo switch and control the NodeMCU using Amazon Alexa (Echo Devices) in addition to the GassistPi.    


************************************************
### **CASTING YouTube VIDEOS TO Chromecast**    
************************************************
Default command for casting YouTube videos is **Play *Desired Video* on Chromecast**, with **Chromecast** as the trigger word.
Example: **Hey Google, Play MasterChef Season 1 Episode 1 on Chromecast** casts the MasterChef YouTube Video.  

**Note: YouTube casting to Chromecast using third party scripts has been blocked, so I have taken a roundabout approach and as a result, you may not find the usual YouTube interface on Chromecast.**  

************************************************
### **CONTROLLING Chromecast BY VOICE**    
************************************************   
First, add the IP-Address of your Chromecast in the actions.py script, in the indicated location.  

Following are the default commands for controlling Chromecast with **Chromecast** as the trigger word.    
Pausing:  
Hey Google, Pause Chromecast  

Resuming:  
Hey Google, Resume Chromecast  

Stopping:
Hey Google, End Chromecast  

Change volume up/down:  
Hey Google, Chromecast Volume Up/Down  


************************************************
### **CCONTROLLING MEDIA BY VOICE**    
************************************************
You can change volume and pause or resume the Radio/YouTube/Google Music by voice.  
Pausing:  
Hey Google, Pause Music  (Entire phrase **Pause Music** is the trigger)

Resuming:  
Hey Google, Resume Music  (Entire phrase **Resume Music** is the trigger)

Volume Control (**Music Volume** is the trigger)

Increase/Decrease Volume:  
Hey Google, Increase/(Decrease or Reduce) Music Volume by ( a number between 0 and 100)   
If you do not specify a number, by default the volume will be increased or decreased by 10 units.  

Set Volume:  
Hey Google, Set/change Music Volume to ( a number between 0 and 100)   

Set volume to Maximum/Minimum:  
Hey Google, Set/change Music Volume to maximum/minimum

Change Tracks:  
Play Previous Track:  
Hey google, play previous  
Hey google, play previous song  
Hey google, play previous track  

Play Next Track:    
Hey google, play next   
Hey google, play next song   
Hey google, play next track   


************************************************
### **MUSIC STREAMING FROM YOUTUBE**  
************************************************
The updated music streaming features autoplaying of YouTube suggestions. This makes use of the YouTube Data API v3.
### Adding YouTube API and Generating API Key
1. Go to the projects page on your Google Cloud Console-> https://console.cloud.google.com/project  
2. Select your project from the list.  
3. On the left top corner, click on the hamburger icon or three horizontal stacked lines.  
4. Move your mouse pointer over "API and services" and choose "credentials".
5. Click on create credentials and select API Key and choose close. Make a note of the created API Key and enter it in the **config.yaml** script at the indicated location.  
6. "From the API and services" option, select library and in the search bar type youtube, select "YouTube Data API v3" API and click on "ENABLE".
7. In the API window, click on "All API Credentials" and in the drop down, make sure to have a tick (check mark) against the API Key that you just generated.

**Note: The same API key can be used for Kickstarter Tracking and Gaana, but Custom Search API must be added to the project in the cloud console.**  

Music streaming has been enabled for both OK-Google and Custom hotwords/wakewords.  

Default keyword for playing music from **YouTube without autoplay** is **Stream**. For example, **Stream I got you** command will fetch Bebe Rexha's I Got You from YouTube.  

Default keyword for playing music from **YouTube with autoplay** is **Autoplay and Stream**. For example, **Autoplay and Stream I got you** command will play the requested I Got You and after the end of the track will autoplay susequent tracks. The number of autoplay tracks has been limited to a maximum of 10. this can be changed the under the YouTube_Autoplay function in the actions.py script.   


| Command Syntax (Hey Google, ...)                   | What it does                                                                 |
|----------------------------------------------------|------------------------------------------------------------------------------|
| Play I got you from youtube                        | Fetches Bebe Rexha's I Got You from YouTube                                  |
| Autoplay I got you from youtube                    | Fetch up to 10 results for **I got you** and play them  all                  |
| Play I got you   playlist  from youtube            | Search for a **playlist** and randomly pick a song                           |
| Autoplay  I got you playlist  from youtube         | Find the **playlist** and fetch up to 10 songs from it                       |
| Play I got you channel from youtube                | Find the **channel** and randomly play a song from it's **uploaded** playlist|
| Autoplay bebe rexha channel from youtube           | Find the **channel** and fetch up to 10 songs from it's **uploaded** playlist|


**Due to the Pi Zero's limitations, users are advised to not use the Music streaming feature. Music streaming will send the CPU usage of Pi Zero into the orbit.**  

************************************************
### **MUSIC STREAMING FROM Google Music**  
************************************************
The music streaming from Google Music uses [Gmusicapi](https://unofficial-google-music-api.readthedocs.io/en/latest/).

Enter your Google userid and password in the **config.yaml** file. If you are using a two-step authentication or two-factor authentication, generate and use an app specific password.

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
### **RADIO STREAMING**  
************************************************
Default keyword for streaming radio is **radio**. For example, **play Radio 2** or **play Radio One** command will open the corresponding radio stream listed in the actions.py file.    

Radio streaming has been enabled for both OK-Google and Custom hotwords/wakewords.

Useful links for obtaining radio streaming links:   
http://www.radiosure.com/stations/  

http://www.live-radio.net/worldwide.shtml  

http://worldradiomap.com/map/  

**Due to the Pi Zero's limitations, users are advised to not use the Radio streaming feature. Radio streaming will send the CPU usage of Pi Zero into next galaxy.**  

***********************************************  
### **PARCEL TRACKING**  
***********************************************  
The default keyword for tracking parcel is **parcel**. For example, you can say **where is my parcel** or **track my parcel**.  

Regsiter for a free account with Aftership at https://www.aftership.com gnereate an API number and add parcels to the tracking list.
The generated API number should be added to the **actions.py** at the indicated location. For a better understanding follow the attached youtube video.

<a href="http://www.youtube.com/watch?feature=player_embedded&v=WOyYL46s-q0
" target="_blank"><img src="http://img.youtube.com/vi/WOyYL46s-q0/0.jpg"
alt="Detailed Youtube Video" width="240" height="180" border="10" /></a>

************************************************  
### **RSS FEEDS STREAMING**  
************************************************  
Default keywords for playing RSS feeds is **feed** or **news** or **quote**. Example usage, **top tech news** will play the top technology news, **top world news** will play top news related to different countires, **top sports news** will play the top sports related news and **quote of the day** will give some quotes.

Do not mix the commands with **Play** as that has been associated with music streaming from YouTube.  

**numfeeds** variable within the feed function in actions.py file is the feed limit. Certain RSS feeds can have upto 60 items and **numfeeds** variable limits the number of items to stream. The default value has been set to 10, which if you want can change.  


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


************************************************  
### **GOOGLE HOME LIKE NEOPIXEL INDICATOR FOR RASPBERRY PI BOARDS**
************************************************  
1. Change the Pin numbers in the given sketch according to your board and upload it.  

2. Follow the circuit diagram given.  

************************************************  
### **LIST OF AVAILABLE LIGHT COLOURS**  
************************************************
|          |                 | COLOURS   | LIST        |             |                   |
|----------|-----------------|-----------|-------------|-------------|-------------------|
| 'Almond' | 'Antique Brass' | 'Apricot' |'Aquamarine' | 'Asparagus' |'Atomic Tangerine' |  
| 'Banana Mania' | 'Beaver' | 'Bittersweet' | 'Black' |'Blizzard Blue' | 'Just Blue' |   
| 'Blue Bell' | 'Blue Gray' | 'Blue Green' | 'Blue Violet' | 'Blush' | 'Brick Red' |  
| 'Brown' | 'Burnt Orange' | 'Burnt Sienna' | 'Cadet Blue' | 'Canary' | 'Caribbean Green' |  
| 'Carnation Pink' | 'Cerise' | 'Cerulean' | 'Chestnut' | 'Copper' | 'Cornflower' |  
| 'Cotton Candy' | 'Dandelion' |'Denim' |'Desert Sand' | 'Eggplant' | 'Electric Lime' |  
| 'Fern' |'Forest Green' | 'Fuchsia' | 'Fuzzy Wuzzy' | 'Gold' | 'Goldenrod' |  
| 'Granny Smith Apple' |'Gray' | 'Just Green' | 'Green Blue' | 'Green Yellow' | 'Hot Magenta' |  
| 'Inchworm' |'Indigo' | 'Jazzberry Jam' | 'Jungle Green' | 'Laser Lemon' | 'Lavender' |  
| 'Lemon Yellow' | 'Macaroni and Cheese' | 'Magenta' | 'Magic Mint' | 'Mahogany' |'Maize' |  
| 'Manatee' | 'Mango Tango' | 'Maroon' | 'Mauvelous' | 'Melon' | 'Midnight Blue' |  
| 'Mountain Meadow' | 'Mulberry' | 'Navy Blue' | 'Neon Carrot' | 'Olive Green' | 'Orange' |  
| 'Orange Red' | 'Orange Yellow' | 'Orchid' | 'Outer Space' | 'Outrageous Orange' | 'Pacific Blue'|  
| 'Peach'| 'Periwinkle'| 'Piggy Pink'| 'Pine Green' | 'Pink Flamingo' | 'Pink Sherbet'|  
| 'Plum' | 'Purple Heart' | "Purple Mountain's Majesty" | 'Purple Pizzazz' | 'Radical Red' | 'Raw Sienna' |  
| 'Raw Umber' |'Razzle Dazzle Rose' | 'Razzmatazz' | 'Just Red' | 'Red Orange' | 'Red Violet' |  
| 'Robin's Egg Blue' | 'Royal Purple' | 'Salmon' | 'Scarlet' | 'Screamin' Green' | 'Sea Green' |  
| 'Sepia' | 'Shadow' | 'Shamrock' | 'Shocking Pink' | 'Silver' | 'Sky Blue' |  
| 'Spring Green' | 'Sunglow' | 'Sunset Orange' | 'Tan' | 'Teal Blue' | 'Thistle' |  
| 'Tickle Me Pink' | 'Timberwolf' | 'Tropical Rain Forest' | 'Tumbleweed' | 'Turquoise Blue' | 'Unmellow Yellow' |  
| 'Violet (Purple)' | 'Violet Blue' | 'Violet Red' | 'Vivid Tangerine' | 'Vivid Violet' | 'White' |  
| 'Wild Blue Yonder' | 'Wild Strawberry' | 'Wild Watermelon' | 'Wisteria' | 'Yellow' | 'Yellow Green' |  
| 'Yellow Orange' |  

************************************************  
### **SENDING VOICE MESSAGES FROM PHONE TO GOOGLE ASSISTANT ON SBCs**  
************************************************
1. https://support.google.com/googlehome/answer/7531913.  

************************************************  
### **LIST OF GPIOs USED IN RASPBERRY PI BOARDS**  
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
