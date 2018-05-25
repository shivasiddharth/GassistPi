---
name: Issue Template
about: Issues to be Reported in this format

---

### Describe the bug
A clear description of what the problem is.

### If the Assistant service is constantly restarting nor not working

**1. Start the Assistant manually using**:

For Pi3+/Pi3/Pi2B and other Armv7 boards:
```
/home/pi/env/bin/python -u /home/pi/GassistPi/src/main.py --device_model_id 'replace this with the model id'
```

For Pi Zero/ZeroW and other Non-Armv7 boards:
```
/home/pi/env/bin/python -u /home/pi/GassistPi/src/pushbutton.py --project-id 'replace this with your project id'  --device-model-id 'replace this with the model id'
```
**2. Copy the contents of the terminal, paste it onto a text file, save it as "Terminal_Contents.txt" and attach the file.**

**3. Attach the log file. Log file can be found in the /tmp directory. Upon restart of Pi the log file will be refreshed, so remember to copy the file when you before restarting or shutting down the Pi.**


### If the Assistant service is running but if the service crashes for a particular command  

**1. Stop the assistant service using:**

For Pi3+/Pi3/Pi2B and other Armv7 boards:
```
sudo systemctl stop gassistpi-ok-google.service
```

For Pi Zero/ZeroW and other Non-Armv7 boards:
```
sudo systemctl stop gassistpi-push-button.service
```

**2. Start the Assistant manually using:**

For Pi3+/Pi3/Pi2B and other Armv7 boards:
```
/home/pi/env/bin/python -u /home/pi/GassistPi/src/main.py --device_model_id 'replace this with the model id'
```

For Pi Zero/ZeroW and other Non-Armv7 boards:
```
/home/pi/env/bin/python -u /home/pi/GassistPi/src/pushbutton.py --project-id 'replace this with your project id'  --device-model-id 'replace this with the model id'
```

**3. Issue the command that crashes/crashed the assistant service.**
Paste the command below:
```

```
**4. Copy the contents of the terminal, paste it onto a text file, save it as "Terminal_Contents.txt" and attach the file.**

**5. Attach the log file. Log file can be found in the /tmp directory. Upon restart of Pi the log file will be refreshed, so remember to copy the file when you before restarting or shutting down the Pi.**
