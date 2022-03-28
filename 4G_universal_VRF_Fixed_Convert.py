import paramiko
import sys
import time
import os
import getpass
import socket
from termcolor import colored
import re
from timeit import default_timer as timer

username = "admin"
password = "admin"

def new_vrf_default_route_check (device_ip):
    try:
        default_route = []
        vrf_default_route = "NOK"

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remote_connection = ssh.connect(device_ip, port="22", username=username, password=password, timeout=10)
        remote_connection = ssh.invoke_shell()
        print(colored("connected_ip_address_" + device_ip, "blue"))
        print(colored("New VRF Default Route Check Started !!" + device_ip, "blue"))

        remote_connection.send("  s 0 t \n")  ## yeni vrf buraya yazılacak
        time.sleep(1)
        remote_connection.send("  dis ip rou vpn 2G4G-DATA-ACCESS 10.186.176.8 \n") ## yeni vrf buraya yazılacak
        time.sleep(3)
        output = remote_connection.recv(65535)
        result = output.decode('ascii').strip("\n")
        print(result)
        output_list_fnk = result.splitlines()

        for line_fnk in output_list_fnk:

            if (("10.186.176.8/29" in line_fnk ) and ( "RD" in line_fnk or "D" in line_fnk)) :
                vrf_default_route = "OK"
                words = line_fnk.split()
                default_route.append(words[0])

        print(vrf_default_route)
        ssh.close()
        return vrf_default_route


    except Exception as e:
        print(device_ip + "no connection_to_device " + str(e), end=" ")
        time.sleep(2)
        with open("unreachables.txt", "a") as f:
            f.write(device_ip + "\n")
            f.close()


def evrensel_vrf_fixed(device_ip):
        file = open("logs/"+device_ip + ".log", "a")


        try:
            vrf_list=[]

            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            remote_connection = ssh.connect(device_ip, port="22", username=username, password=password, timeout=10)
            remote_connection = ssh.invoke_shell()
            print (colored ("connected_ip_address_"+ device_ip,"blue"))

            remote_connection.send("  sys \n")
            time.sleep(2)
            remote_connection.send("  display ip vpn-instance  \n")
            time.sleep(2)
            output = remote_connection.recv(65535)
            result = output.decode('ascii').strip("\n")
            file.write(result)
            output_list_fnk = result.splitlines()
            for line_fnk in output_list_fnk:
                if ("11111" in line_fnk) or ("11111" in line_fnk) :# Vrf  RD  degerleri bölgeler güncelleyecek #
                    words = line_fnk.split()
                    vrf_list.append( words[0])
            print(vrf_list)#bazı bölgelerde birden fazla vrf olması nedeni ile VRF listesi olusturuyoruz #

            for vrf in vrf_list :# VRF altındaki interfaceleri alıyoruz ve bir interface list e atıyotuz #
                interface_list = []
                remote_connection.send("  display ip vpn-instance "+ vrf + " interface  \n")
                time.sleep(2)
                output = remote_connection.recv(65535)
                result = output.decode('ascii').strip("\n")
                print(result)
                file.write(result)
                int1 = re.findall(r'GE(?P<interface>\d/\d/\d{1,2}.+\d+)', result)
                int2 = re.findall(r'GigabitEthernet(?P<interface>\d/\d/\d{1,2}.+\d+)', result)
                int3 = re.findall(r'LoopBack(?P<interface>\d{1,2})', result)
                int4 = re.findall(r'Vlanif(?P<interface>\d{4})', result)  # burada  LoopBack eklendi
                for i in int1:
                    interface_list.append("gigabitethernet"+i)
                for j in int2:
                    interface_list.append("gigabitethernet"+j)
                for k in int3:
                    interface_list.append("LoopBack"+k)
                for w in int4:
                    interface_list.append("Vlanif"+w)
                print(interface_list)
                for interface in interface_list:
                    ######################_interface_traffic_control_before ###################################
                    in_bw_util =0.0
                    out_bw_util =0.0
                    interface_traffic_status_before = "YOK"
                    remote_connection.send("  display interface  " + interface + " \n")
                    time.sleep(4)
                    output2 = remote_connection.recv(65535)
                    result2 = output2.decode('ascii').strip("\n")
                    output_list_fnk22 = result2.splitlines()
                    print(result2)

                    for line_fnk22 in output_list_fnk22:
                        if ("Input bandwidth utilization" in line_fnk22):
                            words2 = line_fnk22.split()
                            in_bw_util=words2[4]
                            in_bw_util=in_bw_util.strip("%")
                            if in_bw_util == "--":
                                in_bw_util="0.0"
                            print(in_bw_util)
                        elif  ("input utility rate" in line_fnk22):
                            words2 = line_fnk22.split()
                            in_bw_util=words2[6]
                            in_bw_util=in_bw_util.strip("%")

                            if in_bw_util == "--":
                                in_bw_util="0.0"
                            print(in_bw_util)
                    for line_fnk23 in output_list_fnk22:
                        if ("Output bandwidth utilization" in line_fnk23) :
                            words3 = line_fnk23.split()
                            out_bw_util=words3[4]
                            out_bw_util =out_bw_util.strip("%")
                            if out_bw_util == "--":
                                out_bw_util = "0.0"
                            print(out_bw_util)
                        elif  ("output utility rate" in line_fnk23):
                            words3 = line_fnk23.split()
                            out_bw_util = words3[6]
                            out_bw_util = out_bw_util.strip("%")
                            if out_bw_util == "--":
                                out_bw_util = "0.0"
                            print(out_bw_util)

                    if ((float(in_bw_util) > 0.01) and( float(out_bw_util) > 0.01)) :
                        print("interface de trafik akısı var ")
                        interface_traffic_status_before = "VAR"
                        print (interface_traffic_status_before)
                    else :
                        print("interface de trafik akısı yok ")

                    time.sleep(2)
                    mac_address_list_before =[]
                    ip_address_list= []

                    remote_connection.send("  display arp interface " + interface + " \n")
                    time.sleep(2)
                    output = remote_connection.recv(65535)
                    result = output.decode('ascii').strip("\n")
                    print(result)
                    output_list_fnk1 = result.splitlines()
                    for line_fnk1 in output_list_fnk1:
                        if  (( vrf in line_fnk1) and ("Incomplete" not in line_fnk1)) :
                            words1 = line_fnk1.split()
                            mac_address_list_before.append(words1[1])
                            ip_address_list.append(words1[0])

                    print(mac_address_list_before)
                    print(ip_address_list)

                    time.sleep(1)
                    interface_ip_address_list =[]
                    remote_connection.send("  display current-configuration interface " + interface + " \n")
                    time.sleep(3)
                    output55 = remote_connection.recv(65535)
                    result55 = output55.decode('ascii').strip("\n")
                    print(result55)
                    output_list_fnk2 = result55.splitlines()
                    for line_fnk2 in output_list_fnk2:
                        if ("ip address" in line_fnk2):  # Interface IP adresi alınıyor #
                            interface_ip_address_list.append(line_fnk2)
                    print("ip_control")
                    print(interface_ip_address_list)


                    #####################Old vrf delete  #############################################

                    remote_connection.send("  interface " + interface + " \n")
                    time.sleep(2)
                    remote_connection.send("  undo ip binding vpn-instance "+ vrf + " \n")
                    time.sleep(2)
                    output = remote_connection.recv(65535)
                    result = output.decode('ascii').strip("\n")
                    print(result)
                    file.write(result)
                    ########################Assign ip address again ########################################
                    remote_connection.send("  ip binding vpn-instance 2G4G-DATA-ACCESS"+" \n")  # Yeni vrf ismi buraya eklenecek

                    time.sleep(2)
                    for ip in interface_ip_address_list:
                        remote_connection.send(ip + " \n")
                    time.sleep(2)
                    remote_connection.send(" commit \n")
                    time.sleep(2)
                    remote_connection.send(" quit \n")
                    time.sleep(2)
                    if len(ip_address_list)> 0 :
                        for w in ip_address_list :
                            remote_connection.send("  ping -m 50 -c 10 -vpn-instance 2G4G-DATA-ACCESS "+ w+" \n")
                            time.sleep(1)
                    output = remote_connection.recv(65535)
                    result = output.decode('ascii').strip("\n")
                    print(result)
                    file.write(result)


                    #############################Mac address list control ################################################
                    i = 0 ;
                    while i < 5 :
                        i =i+1 ;
                        mac_address_list_after = []
                        remote_connection.send("  display arp interface " + interface + " \n")
                        time.sleep(2)
                        output2 = remote_connection.recv(65535)
                        result2 = output2.decode('ascii').strip("\n")
                        output_list_fnk3 = result2.splitlines()

                        for line_fnk3 in output_list_fnk3:
                            if (("2G4G-DATA-ACCESS" in line_fnk3 ) and ("Incomplete" not in line_fnk3)):  # MAC adresleri listesi alınıyor  buraya  gerçek dönüşümde yeni VRF adını yazmamız lazım #
                                words3 = line_fnk3.split()
                                mac_address_list_after.append(words3[1])


                        print(mac_address_list_after)
                        print(i)
                        if (len(mac_address_list_after)  > 2 ) or (len(mac_address_list_after) == len(mac_address_list_before)):

                            break
                        else :
                            print(colored ("Waiting For at least one access site Mac adress ,  Refresh started pls wait 7 seconds !!","yellow"))
                            time.sleep(7)

                    if i== 5 and ((len(mac_address_list_after)  <= 1) or (len(mac_address_list_after) != len(mac_address_list_before))):
                        print(colored ("Migration Failed Pls Control interface " +interface + " Definitions !!!!","red"))
                        f3 = open('convert_nok.txt', 'a')
                        f3.write(device_ip + "\n")
                        f3.close()
                        sys.exit()

                    ######################_interface_traffic_control_after ###################################

                    in_bw_util2 = 0.0
                    out_bw_util2 = 0.0
                    interface_traffic_status_after = "YOK"
                    time.sleep(5)
                    remote_connection.send("  display interface  " + interface + " \n")
                    time.sleep(5)
                    output2 = remote_connection.recv(65535)
                    result2 = output2.decode('ascii').strip("\n")

                    output_list_fnk22 = result2.splitlines()
                    print(result2)


                    for line_fnk22 in output_list_fnk22:
                        if ("Input bandwidth utilization" in line_fnk22):
                            words2 = line_fnk22.split()
                            in_bw_util2 = words2[4]
                            in_bw_util2 = in_bw_util2.strip("%")
                            if in_bw_util2 == "--":
                                in_bw_util2 = "0.0"

                            print(in_bw_util2)
                        elif ("input utility rate" in line_fnk22):
                            words2 = line_fnk22.split()
                            in_bw_util2 = words2[6]
                            in_bw_util2 = in_bw_util2.strip("%")
                            if in_bw_util2 == "--":
                                in_bw_util2 = "0.0"

                            print(in_bw_util2)

                    for line_fnk23 in output_list_fnk22:
                        if ("Output bandwidth utilization" in line_fnk23) :
                            words3 = line_fnk23.split()
                            out_bw_util2 = words3[4]
                            out_bw_util2 = out_bw_util2.strip("%")
                            if out_bw_util2 == "--":
                                out_bw_util2 = "0.0"

                            print(in_bw_util2)

                        elif  ("output utility rate" in line_fnk23):
                            words3 = line_fnk23.split()
                            out_bw_util2 = words3[6]
                            out_bw_util2 = out_bw_util2.strip("%")

                            if out_bw_util2 == "--":
                                out_bw_util2 = "0.0"
                            print(out_bw_util2)



                    if ((float (in_bw_util2) > 0.01) and (float(out_bw_util2) > 0.01)):
                        print("Aktarma sonrası interface de trafik akısı var ")
                        interface_traffic_status_after = "VAR"
                        print(interface_traffic_status_after)
                    else:
                        print("interface de trafik akısı yok ")

                    ###########################trafik akısı öncesi sonrası kontrol #################################

                    if  (interface_traffic_status_after != interface_traffic_status_before) :
                        if  interface_traffic_status_after == "VAR" :
                            print(colored("Migration Successfull For interface  " + interface + " !! ", "blue"))
                            f2 = open('convert_ok.txt', 'a')
                            f2.write(device_ip + "\n")
                            f2.close()
                        else:
                            print(colored("Problem on Convert   " + interface + " !! ", "red"))
                            f3 = open('convert_nok.txt', 'a')
                            f3.write(device_ip + "\n")
                            f3.close()
                            sys.exit()
                    else:
                        print(colored("Migration Successfull For interface  " + interface + " !! ", "blue"))
                        f2 = open('convert_ok.txt', 'a')
                        f2.write(device_ip + "\n")
                        f2.close()
            ssh.close()
        except Exception as e:
            print(device_ip + "no connection_to_device " + str(e), end=" ")
            time.sleep(2)
            with open("unreachables.txt", "a") as f:
                f.write(device_ip + "\n")
                f.close()

while True :
    user_input = str(input("\n\n4G_EVRENSEL_VRF_CONVERT_SCRIPT\n\n""type_1_for_4G_Global_VRF__Convert\ntype_2_for_quit\n"))
    if user_input == "1":
        f1 = open('hostfile.txt', 'r')
        devices = f1.readlines()
        for device in devices:
            column = device.split()
            host = str(column[0])
            t1_start = timer()

            if  new_vrf_default_route_check(host) == "OK" :
                print (colored ("There is no issue in New Vrf Default Route Migration Started !!!", "blue"))
                evrensel_vrf_fixed(host)
            else :
                print(colored(" Control New Vrf Definitions First  !!! Migration Cancelled ", "red"))
                f3 = open('convert_nok.txt', 'a')
                f3.write(host + "\n")
                f3.close()
            t1_stop = timer()

            print("Elapsed time during the whole program in seconds:",
                  int(t1_stop) - int(t1_start))

    elif user_input == "2" :
        print ("Logout....")

        break
