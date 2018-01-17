function end_play(event)
    if event.reason=="eof" then
       os.execute("/home/pi/env/bin/python -u /home/pi/GassistPi/src/trackchange.py")
       print("Script executed")
    else
       print("Closing mpv")
    end
end
mp.register_event("end-file",end_play)
