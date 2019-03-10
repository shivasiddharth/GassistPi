import time
import picamera
import yaml

file_configuration = "/home/pi/GassistPi/recognition/config.yaml"
with open(file_configuration, 'r') as ymlfile:
    configuration = yaml.load(ymlfile)

resolution_x = configuration['status_camera']['resolution']['x']
resolution_y = configuration['status_camera']['resolution']['y']
rotation = configuration['status_camera']['rotation']['degrees']

camera = picamera.PiCamera()
camera.resolution = (resolution_x, resolution_y)
camera.rotation = (rotation)
try:
    camera.start_preview()
    time.sleep(3)
    camera.capture('image.jpg')
    camera.stop_preview()
finally:
    camera.close()
