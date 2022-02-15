import os


def reconnect():
    command = "sudo dhclient -r"
    os.system(command)
    command = "sudo killall wpa_supplicant"
    os.system(command)
    command = "sudo ifconfig wlan0 up"
    os.system(command)
    command = "sudo wpa_supplicant -B -i wlan0 -c /etc/wpa_supplicant/wpa_supplicant.conf"
    os.system(command)
    command = "sudo dhclient -v wlan0"
    os.system(command)


def edit_wpa_supplicant_file(text):
    f = open("/etc/wpa_supplicant/wpa_supplicant.conf")
    lines = f.readline()
    comment = 0
    wpa_file = ""
    f.close()
    for line in lines:
        if line.startswith('#'):
            wpa_file += line
        elif "network" in line:
            comment = 1
        else:
            if comment:
                wpa_file += line
            else:
                wpa_file += ('#'+line)
    wpa_file = wpa_file + '\n\n' + text + '\n'
    # wpa_supp = open("wpa_supp.txt", "w")
    # wpa_supp.write(wpa_file)
    # wpa_supp.close()
    rewrite_file("/etc/wpa_supplicant/wpa_supplicant.conf", wpa_file)
    return wpa_file


def edit_dhcpcd_file(conf):
    f = open("/etc/dhcpcd.conf")
    dhcpcd_text = ""
    start = False
    found = False
    lines = f.readlines()
    for line in lines:
        if not line.startswith('#'):
            if "interface wlan0" in line:
                start = True
                found = True
                print("found : ", found)
        # print("start : ",start)
        if start:
            if "static ip_address" in line:
                i = line.find('=')
                new_line = line[:i+1] + conf['ip'] + '\n'
                dhcpcd_text += new_line
                print(new_line)
            elif "static routers" in line:
                i = line.find('=')
                new_line = line[:i+1] + conf['gateway'] + '\n'
                dhcpcd_text += new_line
                print(new_line)
            elif "static domain_name_servers" in line:
                i = line.find('=')
                new_line = line[:i+1] + conf['dns'] + '\n'
                dhcpcd_text += new_line
                print(new_line)
            elif "interface wlan0" in line:
                dhcpcd_text += line
            elif "interface eth0" in line:
                start = False
                dhcpcd_text += line
        else:
            dhcpcd_text += line
    if not found:
        dhcp_conf = """interface wlan0\nstatic ip_address={}\nstatic routers={}\nstatic domain_name_servers={}""".format(conf['ip'],conf['gateway'],conf['dns'])
        dhcpcd_text += dhcp_conf

    # dhcpcd = open("dhcpcd.txt", "w")
    # dhcpcd.write(dhcpcd_text)
    rewrite_file("/etc/dhcpcd.conf", dhcpcd_text)
    return dhcpcd_text


def remove_static_conf():
    f = open("/etc/dhcpcd.conf")
    dhcpcd_text = ""
    start = False
    found = False
    lines = f.readlines()
    for line in lines:
        if not line.startswith('#'):
            if "interface wlan0" in line:
                start = True
                found = True

            if start:
                if "static ip_address" in line:
                    pass
                elif "static routers" in line:
                    pass
                elif "static domain_name_servers" in line:
                    pass
                elif "interface wlan0" in line:
                    pass
                elif "interface eth0" in line:
                    start = False
                    dhcpcd_text += line
            else:
                dhcpcd_text += line
        else:
            dhcpcd_text += line
    if not found:
        pass

    # dhcpcd = open("dhcpcd.txt", "w")
    # dhcpcd.write(dhcpcd_text)
    rewrite_file("/etc/dhcpcd.conf", dhcpcd_text)
    return dhcpcd_text



def rewrite_file(file_path, text):
    """
    write a new file
    :param file_path: full path and file name of a file ie. /home/user/someFile.json
    :param text: string that to be wrote into the file
    :return:
    """
    try:
        f = open(file_path, 'w+')
        f.write(text)
        f.close()
    except Exception as e:
        raise Exception(e)

# if __name__ == '__main__':
#     reconnect()
