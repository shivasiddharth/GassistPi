
import yaml
import face_recognition
import picamera
import numpy as np
import time
import socket
import paho.mqtt.publish as mqtt


file_configuration = "/home/pi/GassistPi/recognition/config.yaml"
with open(file_configuration, 'r') as ymlfile:
    configuration = yaml.load(ymlfile)

resolution_x = configuration['status_camera']['resolution']['x']
resolution_y = configuration['status_camera']['resolution']['y']
rotation = configuration['status_camera']['rotation']['degrees']
ip_mqtt = configuration['mqtt']['ip_server']

print("mqtt configuration data:")
print("resolution x: " + str(resolution_x))
print("resolution y: " + str(resolution_y))
print("rotation camera: " + str(rotation))
print("ip server address mqtt: " + ip_mqtt)



camera = picamera.PiCamera()
camera.resolution = (resolution_x, resolution_y)
camera.rotation = (rotation)
camera.framerate = 32
output = np.empty((240, 320, 3), dtype=np.uint8)


name = []
references = []
mqtt_person = []


for read in (configuration['known_people']):
    name_person = (list(read)[0])
    file_person = (read[name_person]['file'])
    mqtt_name = (read[name_person]['topic'])
    name = name + [name_person]
    references = references + [file_person]
    mqtt_person = mqtt_person + [mqtt_name]


sample_images = []
a = 0

for images in references:
    sample_image = face_recognition.load_image_file(images)
    sample_images = sample_images + [face_recognition.face_encodings(sample_image)[0]]
    print("I coded " + name[a] + " reference file " + references[a])
    print(" topic " + mqtt_person[a])
    a = a + 1
print("I have completed the encoding of the sample images")


while True:
    print("I capture the image from the PIcamera")
    camera.capture(output, format="rgb")

    # individual the faces present in the image
    identified_faces = face_recognition.face_locations(output)
    print("I found {} faces in the image".format(len(identified_faces)))
    face_encodings = face_recognition.face_encodings(output, identified_faces)

    # cycle for to analyze the faces found
    for face_encoding in face_encodings:
        a = 0
        recognition = 0
        for faces in sample_images:
            comparison = face_recognition.compare_faces([faces], face_encoding)
            if comparison[0] == True and recognition==0:
                print(" ")
                greeting = ("I see "+name[a] + " with file " + references[a] + " topic " + mqtt_person[a])
                print(greeting)
                print(" ")
                try:
                    mqtt.single(mqtt_person[a], name[a], hostname=ip_mqtt)
                except:
                    print("error mqtt")
                recognition = 1
                camera.capture('image.jpg')

            a = a + 1
        if recognition == 0:
            print("unrecognized face")
