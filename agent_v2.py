#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  4 15:23:29 2021

@author: alec
"""
import numpy as np
import matplotlib.pyplot as plt

# time slots are two hours
time_slot_length = 2 

# A function that calculates an arbitary utility function based on an agent's 
# average sleep cycle, and favorite day.
def utility(time_slot, best_day, wake_time, bed_time):
    total_hour = time_slot * time_slot_length # what hour of the week is it
    day_hour = total_hour % 24
    if day_hour < wake_time:
        # print("this time slot is at:", day_hour, 'and I dont wake up until: ', wake_time)
        u= 0
    elif day_hour > bed_time:
        # print("this time slot is at:", day_hour, 'and I go to bed at: ', wake_time)
        u= 0
    else:
        x = time_slot 
        u = (5 * np.cos((np.pi/12)*(x-(12*best_day)))+5) * np.exp(-1*((x-(12*best_day))/30)**2)*abs(np.cos(np.pi*(x-best_day*12)/6))
    return u


# an agent class that is initialized with average bed time, average sleep time, and best day
class agent:
    def __init__(self, id, avg_bt, avg_st, best_day):
        self.average_bedtime = avg_bt
        self.average_sleeptime = avg_st
        self.average_wake_time = (avg_bt+avg_st) % 24
        self.best_day = best_day
        self.id = id
        
        x = list(range(1,85,1))
        # calculate utility for every time slot
        self.u = [ (t, utility(t,self.best_day,self.average_wake_time,self.average_bedtime)) for t in x]
        
        # use the utilities to create a preference ordering
        self.pref_order = sorted(self.u, key=lambda x: x[1], reverse=True)

        
#a = agent(23,8,3)
#x = list(range(1,85,1))
#plt.plot(x,a.u)