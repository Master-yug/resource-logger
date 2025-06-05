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

# Redirect standard output to a log file
log_file = open("system_metrics.log", "w")
sys.stdout = log_file
  
def check_disk_data(disk):
    cdd = shutil.disk_usage(disk)
    print("disk log:\n")
    print ("free =",(cdd.free)/1073741824,"GB")
    print ("used =",(cdd.used)/1073741824,"GB")
    print("")

def virtual_memory_data():
    vmd = psutil.virtual_memory()
    print("virtual memory log:\n")
    print("total =",(vmd.total)/1073741824,"GB")
    print("available =",(vmd.available)/1073741824,"GB")
    print("percent =",(vmd.percent))
    print("used =",(vmd.used)/1073741824,"GB")
    print("")

def swap_memory_data():
    smd = psutil.swap_memory()
    print("swap memory log:\n")
    print ("total =", (smd.total)/1073741824,"GB")
    print ("used =", (smd.used)/1073741824,"GB")
    print ("free =", (smd.free)/1073741824,"GB")
    print ("percent =", (smd.percent),("%"))
    print ("")

def cpu_usage_data():
    print ("cpu log:\n")
    print ("usage =",psutil.cpu_percent(),"%") 
    print ("logical cpu's =", psutil.cpu_count())
    print (psutil.cpu_freq())
    print("")

def netword_usage_data():
    nud = psutil.net_io_counters()
    print ("network log:\n")
    print ("bytes sent =", nud.bytes_sent)
    print ("bytes received =", nud.bytes_recv)
    print ("packets sent =", nud.packets_sent)
    print ("packets received =", nud.packets_recv)
    print ("errors while receiving =", nud.errin)
    print ("errors while sending =", nud.errout)
    print ("incoming packets dropped =", nud.dropin)
    print ("outgoing packets dropped =", nud.dropout)
    print("")

def temperature_sensors_data():
    tsd = psutil.sensors_temperatures()
    print(tsd)

#----output logging        
user_name = getpass.getuser()    
print("USER:",user_name,(""))

curtim = datetime.datetime.now()
print(curtim)

timsta = curtim.timestamp()
print(timsta,"\n")


try:
    check_disk_data("/")
    cpu_usage_data()
    virtual_memory_data()
    swap_memory_data()
    netword_usage_data()
    print("Excecuted successfully!")
except Exception as e:
    print("ERROR GETTING METRICS!")
    traceback.print_exc() # prints stack trace after catching exception
  
log_file.close()    
