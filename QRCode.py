import json

import cv2 #OpenCV in my opinion best library for work with camera
from pyzbar.pyzbar import decode #Zbar - best opensource library for work with QRcode. OpenCV also can it, but not in every build.
import socket
import time
import os
import script
from pynput import keyboard
import threading

RPicamera = False #also can work with RPiCamera
if RPicamera:
    from picamera.array import PiRGBArray
    from picamera import PiCamera


#ForTestReasons
def DecideParams():
    try:
        if os.uname()[4][:3] == 'arm':
            print('RPi found')
            Platform='RPiOS'
        else:
            print('CPU found, unix')
            Platform = 'UNIX'
    except:
        Platform = 'WIN'
    return Platform

#Simple check if internet is online
def is_connected():
    try:
        # connect to the host -- tells us if the host is actually
        # reachable
        socket.create_connection(("www.google.com", 80))
        return True
    except OSError:
        pass
    return False

#Check if ARM
Platform = DecideParams()
testmod = True #To test on Windows machine without connections

# Salimi Code
is_stop = False

def init_key_file(file_path=""):
    with open(file_path + "register_state", "w") as f:
        f.write("1")

def read_init_key_file(file_path=""):
    with open(file_path + "register_state", "r") as f:
        return f.read(1)

def set_init_key_file(file_path, values):
    with open(file_path + "register_state", "w") as f:
        f.write(values)
        print("set init file to " + str(values))

def on_press(key):
    try:
        # print('Alphanumeric key pressed: {0} '.format(key.char))
        if key.char == 'a':
            set_init_key_file("", "0")
        elif key.char == 's':
            set_init_key_file("", "1")
    except AttributeError:
        print('special key pressed: {0}'.format(key))

def on_release(key):
    # print('Key released: {0}'.format(key))
    if key == keyboard.Key.esc:
        # Stop listener
        return False

def create_conf_string(ssid, psk):
    return """network={\n\tssid="%s"\n\tscan_ssid=1\n\tpsk="%s"\n\tkey_mgmt=WPA-PSK\n}""" % (ssid, psk)

def ThreadLoop():
    while not is_stop:
        init_key = read_init_key_file("")
        if init_key == "0":
            print("idle")
            time.sleep(1)
        elif init_key == "1":
            if Platform=='RPiOS' or Platform=='UNIX' or testmod:
                isconnect=False
                #Try to connect for 60 seconds. If no connection found - start process
                if not testmod:
                    time_start = time.time()
                    isconnect = is_connected()
                    try_to_connect = not isconnect
                    while try_to_connect:
                        time.sleep(5)
                        if time.time()-time_start<60:
                            try_to_connect=False
                        if is_connected():
                            try_to_connect=False
                #if machine not connected to internet or in testmode
                if testmod or not isconnect:
                    #if we have RPi camera - we can use it
                    if RPicamera:
                        camera = PiCamera()
                        camera.resolution = (640, 480)
                        camera.framerate = 32
                        rawCapture = PiRGBArray(camera, size=(640, 480))
                        time.sleep(0.1)
                    else:
                        cap = cv2.VideoCapture(0)

                    timestamp = -1
                    continue_search=True
                    last_check_time = time.time()
                    while continue_search:
                        #if we have RPI camera
                        if RPicamera:
                            rawCapture.truncate(0)
                            image = next(camera.capture_continuous(rawCapture, format="bgr", use_video_port=True)).array
                        else:
                            was_read, image = cap.read()
                        #After we find QRCode - we stop deterction for 20 secondes, or it will be continius reconnect attemps
                        if time.time()-timestamp>20:
                            data = decode(image) #Search for codes
                            if len(data) > 0:
                                qr_string = data[0].data.decode("utf-8")
                                try:
                                    wifi_conf = json.loads(qr_string)
                                    print(wifi_conf)
                                    ssid = wifi_conf['ssid']
                                    pas = wifi_conf['psk']
                                    print("Detected! -> ssid: " + ssid + ', pass: ' + pas)
                                    script.edit_wpa_supplicant_file(create_conf_string(ssid,pas))
                                    if 'static' in wifi_conf.keys():
                                        print(wifi_conf['static'])
                                        script.edit_dhcpcd_file(json.dumps(wifi_conf['static']))
                                    else:
                                        print("DHCP")
                                    script.reconnect()
                                    set_init_key_file("", "0")
                                    cap.release()
                                    cv2.destroyAllWindows()
                                    break
                                except Exception as e:
                                    print(e, "\nInvalid QR Code")
                                    # raise TypeError("Invalid QR Code")
                            else:
                                print("NotFound")
                        else:
                            time.sleep(1)
                            if not testmod:
                                continue_search = not is_connected()
                        if Platform!='RPiOS': # if not RPi - visualisation
                            cv2.imshow("depth", image)
                            cv2.waitKey(10)
                        else:
                            if not testmod: # if not testmode - try to connect
                                if time.time() - last_check_time>5:
                                    continue_search = not is_connected()
                                    last_check_time = time.time()

thread_obj = threading.Thread(target=ThreadLoop)
thread_obj.start()

# Collect events until released
with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
    listener.join()

thread_obj.join()

# if __name__ == '__main__':
#     print(create_conf_string("singo", """sd'd"""))