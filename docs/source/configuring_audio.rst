*****************
Configuring Audio
*****************

Update OS 
---------

.. prompt:: bash $

    sudo apt-get update


Restart Pi  and change directory  
--------------------------------

.. prompt:: bash $

    cd /home/${USER}/   


Choose the audio configuration according to your setup.   
------------------------------------------------------

**Non-Raspberry Pi users, choose the USB-DAC option.    
  The speaker-test command is used to initialize alsa, so please do not skip that.  
  AIY-HAT and CUSTOM-HAT users, please reboot the Pi at places mentioned, else it will lead to audio and taskbar issues.**  

USB DAC or USB Sound CARD users 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. prompt:: bash $

       sudo chmod +x ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh  
       sudo ./GassistPi/audio-drivers/USB-DAC/scripts/install-usb-dac.sh
       speaker-test     



AIY-HAT users  
~~~~~~~~~~~~~    

.. prompt:: bash $

        sudo chmod +x ./GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
        sudo ./GassistPi/audio-drivers/AIY-HAT/scripts/configure-driver.sh  
        sudo reboot  
        cd /home/${USER}/  
        sudo chmod +x ./GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
        sudo ./GassistPi/audio-drivers/AIY-HAT/scripts/install-alsa-config.sh  
        speaker-test     
 


USB MIC AND HDMI users
~~~~~~~~~~~~~~~~~~~~~~   

.. prompt:: bash $

        sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/configure.sh  
        sudo ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/configure.sh  
        sudo reboot  
        cd /home/${USER}/  
        sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
        sudo ./GassistPi/audio-drivers/USB-MIC-HDMI/scripts/install-usb-mic-hdmi.sh  
        speaker-test
      


USB MIC AND AUDIO JACK users  
~~~~~~~~~~~~~~~~~~~~~~~~~~~~  
.. prompt:: bash $

         sudo chmod +x ./GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
         sudo ./GassistPi/audio-drivers/USB-MIC-JACK/scripts/usb-mic-onboard-jack.sh  
         speaker-test  
     
     
     
CUSTOM VOICE HAT users
~~~~~~~~~~~~~~~~~~~~~~

.. prompt:: bash $

         sudo chmod +x ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh  
         sudo ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/install-i2s.sh
         sudo reboot  
         cd /home/${USER}/  
         sudo chmod +x ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
         sudo ./GassistPi/audio-drivers/CUSTOM-VOICE-HAT/scripts/custom-voice-hat.sh  
         speaker-test   


RESPEAKER HAT users  
~~~~~~~~~~~~~~~~~~~

.. prompt:: bash $

     git clone https://github.com/shivasiddharth/seeed-voicecard
     cd ./seeed-voicecard/  
     sudo ./install.sh  
     sudo reboot   
     speaker-test
         


**Those using any other DACs or HATs install the cards as per the manufacturer's guide
 and then you can try using the USB-DAC config file after changing the hardware ids**   
     
