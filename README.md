
![github-small](https://user-images.githubusercontent.com/18142081/84596026-d7ea8180-ae78-11ea-938f-5911cf7771ce.png)

# Google Assistant and Volumio Speaker Integration   
*******************************************************************************************************************************
### **If you like the work, find it useful and if you would like to get me a :coffee: :smile:** [![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=7GH3YDCHZ36QN)

### Do not raise an Issue request for Non-Issue stuff. For Non-Issue Help and Interaction use gitter [![Join the chat at https://gitter.im/publiclab/publiclab](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/GassistPi/Lobby/)  

*******************************************************************************************************************************

### NOTE: "${USER}" will automatically take your username. No need to change that. Just copy pasting the following commands on terminal will work.  

*************************************************    
## **CONNECTING TO VOLUMIO via SSH**      
*************************************************  
1.  By default, SSH is disabled. To enable SSH, open the Volumio client's developer console from a browser using:  
```  
http://ADDRESS_OF_YOUR_VOLUMIO/dev
```   

2. In that window, under SSH, choose Enable.   

3. Now You can connect to the Volumio client via SSH using a software like Putty.   

*************************************************    
## **ADD RASPBIAN SOURCES**      
*************************************************   
1. Open the sources list using:   
```
sudo nano /etc/apt/sources.list
```

2. Add the following lines:   
```   
deb http://mirrordirector.raspbian.org/raspbian/ stretch main contrib non-free rpi firmware
deb http://archive.raspberrypi.org/debian/ stretch main ui
```   

3. Press **Ctrl+X** followed by **Y** and **Enter/Return** to save and exit.

4. Update using (must, do not skip):
```   
sudo apt-get update
```   

*************************************************
## **CLONE the PROJECT on to Pi**   
*************************************************
1. Open the terminal and execute the following  

```
sudo apt-get install git  
sudo apt-get install alsa-utils   
git clone https://github.com/shivasiddharth/GassistPi -b Volumio
```

*************************************************    
## **CONFIGURE AUDIO IN VOLUMIO**    
*************************************************   
1. Configure your audio output device according to your setup as shown below.    

<img src="https://drive.google.com/uc?id=1LnDG0GyQg5T-StvfNn_Yq0E9kaLTBbqd"   
width="600" height="400" border="1" />     

2. If you are using an USB DAC or an I2S DAC:    
**Note: Anytime you make changes to the volume configuration, it will change the audio device setting. So you need to change the device option as mentioned in the steps below.**    

2.1 In the volume options, change the **Mixer Type** to **Software** as shown below. Otherwise set it to     **Hardware**.      

<img src="https://drive.google.com/uc?id=1OrxUnLeTyWDJEOuvxNwDOXzlHn09BnQA"   
width="600" height="400" border="1" />    

2.2 . Open Volumio configuration using:   
```
sudo nano /etc/mpd.conf    
```

2.3 . Under audio_output option, change the device to **"plug:dmixer"**    

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

3.1. USB DAC or USB Sound CARD users,  
```
sudo chmod +x ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
sudo ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh
```

3.2. USB MIC AND HDMI users,  
```
sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/configure.sh  
sudo ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/configure.sh  
sudo reboot  
cd /home/${USER}/  
sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
sudo ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
```

3.3. USB MIC AND AUDIO JACK users,  
```  
sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
sudo ./GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
```             

**Note: Any other I2S DAC users, choose USB DAC Option**   

4. Check the audio in and out device or card numbers using:
```
arecord -l   
aplay -l    
```  

5. Open the .asoundrc and asound.conf files one by one using:
```
sudo nano ./.asoundrc   
sudo nano /etc/asound.conf  
```  
Change the device card numbers in the files depending upon the numbers that you got from Step-4 above.  

6. Restart Pi

7. Check the speaker using the following command    

```
speaker-test -t wav  
```  

**********************************************************************  
## **INSTALLING GOOGLE ASSISTANT**
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

6. After successful authentication, the Google Assistant installation will finish.   


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
/home/${USER}/env/bin/python -u /home/${USER}/GassistPi/src/main.py --project_id 'replace this with the project id' --device_model_id 'replace this with the model id'

```

Insert your Project Id and Model Id in quotes in the mentioned places      

### DISABLING AUTO-START ON BOOT      

At any point of time, if you wish to stop the auto start of the assistant:      

Open a terminal and execute the following:     
```
sudo systemctl stop gassistpi.service  
sudo systemctl disable gassistpi.service   
```    
