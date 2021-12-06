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
time_slot_interval = 10 # minutes between each laundry use

# a function with domain [-5400,5400] with preferences centered at x=0 for noon
# of a favorite day
#   relative_time: minutes before (-) or minutes after (+) noon on favorite day
#   p: frequency, a random integer between 200 and 500 indicating the period of 
#      a students classes

def relative_utility(relative_time, p):
    favoritism = np.exp(-1*(relative_time/4000)**2)
    avail_days = 5 * np.cos(np.pi*relative_time/1440) + 5
    sched = np.cos(np.pi*relative_time/p) + 1
    return favoritism * avail_days * sched

# a function that takes a students randomized properties and calculates their
# entire utility function over the domain [0,10800] interpreted as minutes past
# 12pm Sunday.
def all_utility(best_day, wake_time, bed_time, p):
    
    # intialize the relative domain and calculate the relative utilit
    x = list(range(-5400,5400,1))
    u1 = np.array([relative_utility(t,p) for t in x])
    
    # if the preferred day is after wednesday, then the index of noon on sunday
    # is 5400(which is x=0 relative utility) + (# of days past wednesday)*1440
    if best_day > 3:
        u1 = np.concatenate([u1[5400+(best_day-3)*1440:], u1[:5400+(best_day-3)*1440]])
    elif best_day < 3:
        u1 = np.concatenate([u1[5400-(best_day)*1440:], u1[:5400-(best_day)*1440]])
    
    # if they have a late bedtime
    if bed_time < 4:
        for i in range(7):
            u1[i*1440+(bed_time + 12)*60:i*1440+(wake_time + 12)*60+1] = 0
    else:
        for i in range(7):
            u1[i*1440+(bed_time-12)*60:i*1440+(wake_time + 12)*60+1] = 0
    
    return u1
    

# an agent class that is initialized with average bed time, average sleep time, and best day
class agent:
    def __init__(self, agent_id, avg_bt, avg_st, best_day, p):
        self.average_bedtime = avg_bt
        self.average_sleeptime = avg_st
        self.average_wake_time = (avg_bt+avg_st) % 24
        self.best_day = best_day
        self.id = agent_id
        self.p = p
        self.allocated_timeslot = None
        
        # calculate utility for every time slot
        self.u = all_utility(self.best_day,self.average_wake_time,self.average_bedtime,p)
        self.u_pairs = [(i,self.u[i]) for i in range(10800) if i % time_slot_interval == 0]
        # use the utilities to create a preference ordering
        self.pref_order = sorted(self.u_pairs, key=lambda x: x[1], reverse=True)

    def reorder_preferences(self, t):
        self.u[t] = 0
        self.u_pairs = [(i,self.u[i]) for i in range(10800) if i % time_slot_interval == 0]
        self.pref_order = sorted(self.u_pairs, key=lambda x: x[1], reverse=True)

        
a = agent(99,23,8,1,300)
#print(a.pref_order)
#x = list(range(0,1080,1))
#plt.plot(x,a.u)