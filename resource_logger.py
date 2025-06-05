#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  3 20:57:53 2025

@author: master-yug
"""
import shutil
import psutil
import getpass
import sys
import datetime
import traceback
import csv
import statistics as st
import os

# Redirect standard output to a log file
log_file = open("system_metrics.log", "w")
sys.stdout = log_file

if not os.path.exists("system_metrics.csv"):
    # create csv and write column header if not exists yet
    with open("system_metrics.csv", "w") as f:
        f.write("time,disk_used,disk_free,cpu_usage,cpu_freq,avg_cpu_temp,mem_total,mem_used,mem_free,swp_total,swp_used,swp_free,net_bytes_sent,net_bytes_recv,net_packets_sent,net_packets_recv,net_errors_out,net_errors_in,net_packetdrop_out,net_packetdrop_in\n")

# open csv file
csv_file = open("system_metrics.csv", "a")
csv_w = csv.writer(csv_file)

def check_disk_data(disk):
    cdd = shutil.disk_usage(disk)
    free = round((cdd.free)/1073741824, 2)
    used = round((cdd.used)/1073741824, 2)
    print("disk log:")
    print ("used =", used, "GB")
    print ("free =", free, "GB")
    print()
    return used, free

def virtual_memory_data():
    vmd = psutil.virtual_memory()
    total = round((vmd.total)/1073741824, 2)
    free = round(vmd.available/1073741824, 2)
    used = round((vmd.used)/1073741824, 2)
    print("virtual memory log:")
    print("total =", total, "GB")
    print("used =", used, "GB")
    print("free =", free, "GB")
    print("percent =", (vmd.percent))
    print()
    return total, used, free

def swap_memory_data():
    smd = psutil.swap_memory()
    total = round(smd.total/1073741824, 2)
    used = round(smd.used/1073741824, 2)
    free = round(smd.free/1073741824, 2)
    print("swap memory log:")
    print ("total =", total, "GB")
    print ("used =", used, "GB")
    print ("free =", free, "GB")
    print ("percent =", smd.percent, "%")
    print ()
    return total, used, free

def cpu_usage_data():
    usage = psutil.cpu_percent()
    core_count = psutil.cpu_count()
    freq = round(psutil.cpu_freq().current/1000, 2)
    print ("cpu log:")
    print ("usage =", usage, "%") 
    print ("logical cpu's =", core_count)
    print ("frequency =", freq, "GHz")
    print()
    return usage, freq, core_count

def netword_usage_data():
    nud = psutil.net_io_counters()
    print("network log:")
    b_sent = nud.bytes_sent
    b_recv = nud.bytes_recv
    p_sent = nud.packets_sent
    p_recv = nud.packets_recv
    e_sent = nud.errout
    e_recv = nud.errin
    pd_out = nud.dropout
    pd_in = nud.dropin
    print("bytes sent =", b_sent)
    print("bytes received =", b_recv)
    print("packets sent =", p_sent)
    print("packets received =", p_recv)
    print("errors while sending =", e_sent)
    print("errors while receiving =", e_recv)
    print("outgoing packets dropped =", pd_out)
    print("incoming packets dropped =", pd_in)
    print()
    return (b_sent, b_recv, p_sent, p_recv, e_sent, e_recv, pd_out, pd_in)

def temperature_sensors_data():
    tsd = psutil.sensors_temperatures()
    temp_data = {}
    print("temperature log:")
    for categ in tsd:
        print(categ+":")
        temp_data[categ] = {}
        for i in tsd[categ]:
            temp_data[categ][i.label] = round(i.current, 2)
            print(f"  {i.label} = {i.current}°C")
    print()
    return temp_data

# script run entry point
if __name__ == "__main__":
    #----output logging
    user_name = getpass.getuser()
    print("USER:", user_name)

    curtim = datetime.datetime.now()
    print(curtim)

    timsta = curtim.timestamp()
    print(timsta,"\n")

    try:
        disk_data = check_disk_data("/")
        cpu_data = cpu_usage_data()
        mem_data = virtual_memory_data()
        swp_data = swap_memory_data()
        net_data = netword_usage_data()
        temp_data = temperature_sensors_data()
        avg_cpu_temp = st.mean(temp_data["coretemp"].values()) if temp_data.get("coretemp") else None
        csv_w.writerow([
            curtim.isoformat(),
            disk_data[0],
            disk_data[1],
            cpu_data[0],
            cpu_data[1],
            avg_cpu_temp,
            mem_data[0],
            mem_data[1],
            mem_data[2],
            swp_data[0],
            swp_data[1],
            swp_data[2],
            net_data[0],
            net_data[1],
            net_data[2],
            net_data[3],
            net_data[4],
            net_data[5],
            net_data[6],
            net_data[7],
        ])
        print("Excecuted successfully!")
    except Exception as e:
        print("ERROR GETTING METRICS!")
        traceback.print_exc() # prints stack trace after catching exception
    
    log_file.close()
