from Tkinter import Tk, Label, Button , Frame
from PIL import Image , ImageTk
from io import BytesIO
import base64
from datetime import datetime
import requests
import bluetooth._bluetooth as bluez
import json
import io
import time
# from Utility import Utility
import threading
from functools import partial
import blescan
import sys
import re
import serial
import urllib
red = "1016255001001"
LocalHost="localhost"
ConfigFilePath="/home/pi/TAT/Config.json"
dev_id = 0
socket = ""
LatLong = ""
DeviceId = ""
mode = 0
min_pwr = -35
display_list = 8
uuid_list = []
label_list = []
att_dict = {}

try:
    sock = bluez.hci_open_dev(dev_id)
    print "ble thread started"
except:
    print "error accessing bluetooth device..."
    sys.exit(1)

blescan.hci_le_set_scan_parameters(sock)
blescan.hci_enable_le_scan(sock)

# utility = Utility(log_file="gui_app_logfile.txt", debug=1)
# utility.loginfofile("Initializing app..........................")
print ("Initializing app..........................")
# tk_list = [None]
tk_list = [] #{"organization":"Project Manager","name": "sushant", "card_number": "XXXXX548", "datetime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "image":""}

def WriteToUart(datainput):
    ser = serial.Serial(port='/dev/ttyS0', baudrate = 9600, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS, timeout=1)
    try:
        # count = 3+ blink_time
        # for i in range(count):
        # print "WriteToUart"
        ser.write(datainput+'#')
        time.sleep(0.5)
        ser.write("1016001001001"+'#')
        time.sleep(0.5)
    except:
        print "Error in writing to Serial - UART"
        return "NK"

def update():
    root.update()
    root.after(1000, update)


# def clear_layout():
#     for i in range(display_list):
#         self.label = Label()

def post_attendance(uuid,scan_datetime,master):
    try:
        re = requests.post("http://trackmii.in:9090/Employee/v1_0/postEmployeeAttendance", data={'uuid':uuid, 'timestamp':scan_datetime})
        #re = requests.post("http://192.168.1.200:8000/Employee/v1_0/postEmployeeAttendance", data={'uuid':uuid, 'timestamp':scan_datetime})
        print re.status_code
        if re.status_code != 200:
            print ("'{}' not entered/exit".format(uuid))
            return None

        resp = re.json()
        print "---------------",resp["result"]["enter_time"], resp["result"]["exit_time"]
        
        time.sleep(2)

        for obj in tk_list:
            if obj["card_number"] == uuid:
                obj["enter_datetime"] = scan_datetime[:11] + resp["result"]["enter_time"]
                if resp["result"]["exit_time"]:
                    obj["exit_datetime"] = scan_datetime[:11] + resp["result"]["exit_time"]

        print obj
        my_gui.generate_frame(master)
    except Exception as e:
        print e
#fetch details for scanned uuid
def get_info(master,uuid, t2, scan_time, scan_datetime):
    # get info for scan id card
    # util = Utility(log_file="gui_app_logfile.txt", debug=1)
    # util.loginfofile("new beacon found......")
    print (threading.currentThread().getName() + "initiated")
    print t1
    global uuid_list , display_list
    try:
        re = requests.post("http://trackmii.in:9090/Employee/v1_0/employee_info", data={'uuid': uuid})
        #re = requests.post("http://192.168.1.200:8000/Employee/v1_0/employee_info", data={'uuid': uuid})
    except Exception as e:
        print ("Network Error.....")
        uuid_list.remove(uuid)
        return None
    # util.loginfofile(" fetching........ info for emp-id '{}' ".format(uuid))
    # util.loginfofile(str(re.status_code))
    if re.status_code != 200:
        print ("'{}' not registered".format(uuid))
        uuid_list.remove(uuid)
        return None
    resp = re.json()
  
    # light led
    WriteToUart(red)
    # fetching employee info
    if resp['type'] == 'emp':
        global firstname, lastname
        firstname = resp['emp_info']["emp_first_name"]
        lastname = resp['emp_info']["emp_last_name"]
        name = firstname + " " + lastname
        card_id = resp["emp_info"]["emp_card_id"]
        organization = resp["emp_info"]["organization"]
        emp_id = resp["emp_info"]["emp_number"]
    # utility.loginfofile("emp found with name '{}'".format(name))
    if resp['type'] == 'asset':
    # fetching card info
        name = resp['asset_info']['asset_name']
        card_id = resp["asset_info"]["asset_card_id"]
        organization = ""
        emp_id = ""

    # #instant display image
    # im = Image.open("/home/pi/TAT/no-image-landscape.png")
    # im = im.resize((100, 80), Image.ANTIALIAS)
    # image = ImageTk.PhotoImage(im)
    # add uuid info in gui app memory(tk_list)
    t3 = datetime.now()
    image = ""
    disp_details = {}
    disp_details["name"] = name
    disp_details["card_number"] = card_id
    disp_details["image"] = image
    disp_details["organization"] = organization #scan_time 
    disp_details["emp_id"] = emp_id
    disp_details["enter_datetime"] = scan_datetime
    disp_details["exit_datetime"] = '' #t3-t2 


    # map display list
    if len(tk_list) >= display_list:
        tk_list.pop()
    tk_list.insert(0,disp_details)   
    print tk_list

    #refresh app grid
    my_gui.generate_frame(master)
    # time stamp
    
    # fetching image
    # img = resp['emp_info']["base64_image"]
    try:
        img = resp['emp_info']["image_link"]
    except Exception, e:
        print ("asset found")
        img = ""

    print img
    if img:
        # im = Image.open(BytesIO(base64.b64decode(img)))
        try:
            fd = urllib.urlopen(img)
            img = io.BytesIO(fd.read())
            im = Image.open(img)
            im = im.resize((100, 80), Image.ANTIALIAS)
            image = ImageTk.PhotoImage(im)
        except Exception, e:
            im = Image.open("/home/pi/TAT/no-image-landscape.png")
            im = im.resize((100, 80), Image.ANTIALIAS)
            image = ImageTk.PhotoImage(im)


    #update image for received uuid
    for obj in tk_list:
        if obj["card_number"] == uuid:
            obj["image"] = image

    # refresh display_list
    if threading.active_count() <= 2:
        print ("refreshing display_list")
        uuid_list = map(lambda x: x["card_number"], tk_list)

    #refresh app grid
    my_gui.generate_frame(master)
    


def start_scan(socket, DeviceId, mode, sock, master):
    # utility.loginfofile("Thread initiated for scanning........." + str(threading.currentThread().getName()))
    print ("scanning............")
    global uuid_list
    while True:
        #scan for beacon (uuid)
        # time stamp
        t1 = datetime.now()
        returnedList = blescan.parse_events(socket, DeviceId, LatLong, mode, sock, 10)
        for beac in returnedList:
            uuid, rssi = re.findall(r"[\w^-]+", beac)[:2]
            print uuid, (rssi)
            #if new beacon found
            print (uuid_list)
            #post attendance for uuid
            scan_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if int(rssi) > min_pwr and uuid not in uuid_list:
                t2 = datetime.now()
                scan_time = t2-t1
                print ("'{}' took to scan".format(scan_time))
                uuid_list.append(uuid)
                print ("fetching deatils for uuid: '{}'".format(uuid))
                # uuid_list.append(uuid)
                # call get_info(uuid)
                thread1 = threading.Thread(name="get_info_thread_for_'{}'".format(uuid[-5:]), target=get_info, args=(master,uuid, t2, scan_time, scan_datetime))
                thread1.setDaemon(True)
                thread1.start()

            if uuid not in att_dict.keys() and int(rssi) > min_pwr:
                att_thread = threading.Thread(name="attendance_thread_for_{}".format(uuid[-5:]), target=post_attendance(uuid,scan_datetime,master))
                att_dict[uuid] = scan_datetime
            if uuid in att_dict.keys() and int(rssi) > min_pwr:
                time_diff = (datetime.now().replace(microsecond=0) - datetime.strptime(att_dict[uuid], "%Y-%m-%d %H:%M:%S")).total_seconds()
                print "----------", time_diff
                if int(time_diff) >=30:
                    print ("marking entry for {}".format(uuid))
                    att_thread = threading.Thread(name="attendance_thread_for_{}".format(uuid[-5:]), target=post_attendance(uuid,scan_datetime,master))
                    att_dict[uuid] = scan_datetime
                else:
                    print ("scanned in less then 30 sec")

        # if threading.active_count() <= 2:
        #     print "-----clearing frame----------"
        #     my_gui.clear_frame()
    

class BTASGUI:
    def __init__(self, master, tk_list):

        self.master = master
        master.title("BTAS")
        self.tk_list = tk_list
        self.label = Label(master, text="Image", font="Verdana 10 bold")
        self.label.grid(row=0, columnspan=2)
        self.name = Label(master, text="Name", font="Verdana 10 bold")
        self.name.grid(row=0, column=5, columnspan=5,padx=10, pady=5)
        self.card_id = Label(master, text="Card ID", font="Verdana 10 bold")
        self.card_id.grid(row=0, column=10, columnspan=5,padx=10, pady=5)
        self.empid = Label(master, text="Emp-Id", font="Verdana 10 bold")
        self.empid.grid(row=0, column=15, columnspan=3, padx=10, pady=5)
        self.organization = Label(master, text="Organization", font="Verdana 10 bold")
        self.organization.grid(row=0, column=20, columnspan=3, padx=10, pady=5)
        self.in_time = Label(master, text="In-Time", font="Verdana 10 bold")
        self.in_time.grid(row=0, column=25, columnspan=3,padx=10, pady=5)
        self.out_time = Label(master, text="Out-Time", font="Verdana 10 bold")
        self.out_time.grid(row=0, column=30, columnspan=3,padx=10, pady=5)

        # self.frame = Frame(root)
        # self.frame.pack(side="left")

        # self.label = Label(self.frame1, text="Your checkin time is " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        # self.label.pack(ipadx=20)

        # self.generate_frame(master)

        # self.load_button = Button(self.frame1, text="Load Image", command=self.load)
        # self.load_button.pack()
        #
        # self.close_button = Button(self.frame1, text="Close", command=master.quit)
        # self.close_button.pack()

    def generate_frame(self, master):
        #clear frame
        self.clear_frame()
       
        for i in range(len(tk_list)):
            image = Label(master, image=tk_list[i]["image"])
            image.grid(row=i+1, columnspan=3, padx=10, pady=5)
            label_list.append(image)
            name = Label(master, text=tk_list[i]["name"])
            name.grid(row=i+1, column=5, columnspan=5,padx=10, pady=5)
            label_list.append(name)
            card_id = Label(master, text=tk_list[i]["card_number"][-5:])
            card_id.grid(row=i+1, column=10, columnspan=5,padx=10, pady=5)
            label_list.append(card_id)
            emp_id = Label(master, text=tk_list[i]["emp_id"])
            emp_id.grid(row=i+1, column=15, columnspan=5,padx=10, pady=5)
            label_list.append(emp_id)
            organization = Label(master, text=tk_list[i]["organization"])
            organization.grid(row=i+1, column=20, columnspan=5,padx=10, pady=5)
            label_list.append(organization)
            in_time = Label(master, text=tk_list[i]["enter_datetime"])
            in_time.grid(row=i+1, column=25, columnspan=3,padx=10, pady=5)
            label_list.append(in_time)
            out_time = Label(master, text=tk_list[i]["exit_datetime"])
            out_time.grid(row=i+1, column=30, columnspan=3,padx=10, pady=5)
            label_list.append(out_time)

    def clear_frame(self):
        print "-----clearing frame----------"
        for label in label_list: label.destroy()





    # def load(self):
    #     pass

    # def loadImage(self):
          #pass

#gui app configurations
root = Tk()
root.geometry("850x600")

#initiate scanning thread
t1 = threading.Thread(name="ble_scan_thread", target=start_scan, args=(socket, DeviceId, mode, sock, root))
t1.setDaemon(True)
t1.start()

#initiate app
my_gui = BTASGUI(root, tk_list)
root.after(1000, update)
root.mainloop()



# imgFile1 = "/home/sushant/Desktop/"
# img1 = Image.open(imgFile1)
# image1 = img1.resize((250, 250), Image.ANTIALIAS)
# img_n = ImageTk.PhotoImage(image1)
# self.panel = Label(self.frame, image = img_n)
# self.panel.pack(side = "left", fill = "both", expand = "yes")


# print "Loading Images......"
# url = "http://cdn-payscale.com/cms-images/default-source/Blogs/dan-kalish.jpg"
# fd = urllib.urlopen(url)
# imgFile = io.BytesIO(fd.read())


# xauth list | grep unix`echo $DISPLAY | cut -c10-12` > /tmp/xauth
# sudo su
# xauth add `cat /tmp/xauth`
# exit