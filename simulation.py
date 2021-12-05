#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  4 16:19:11 2021

@author: alec
"""
import random
from agent_v2 import agent

# number of agents in the simulation
n = 100

# number of washer machines
m = 2

# randomize agent preferences REVISIT 
fave_days = random.choices(list(range(0,7,1)),k=n)
bed_times = random.choices([20,21,22,23,24,1,2,3],k=n)
sleep_times = random.choices([6,7,8,9],k=n)

# intialize agents
agents = { i: agent( i, bed_times[i], sleep_times[i], fave_days[i]) for i in range(n)}

# runs a single round of random serial dictatorship
def single_RSD(agents):
    
    # randomize the order
    order = list(agents.keys())
    random.shuffle(order)

    # dict of (time slot #, list of allocated agents)
    allocation = {}
    total_utility = 0
    
    # iterate over agents in order
    for agent in list(order):

        prefs = agents[agent].pref_order
        allocated = False
        i = 0
        
        while allocated == False:
            
            # current top preference
            top = prefs[i][0]
            util = prefs[i][1]
            
            # check if their current top preference is still available
            if top in allocation.keys():
                if len(allocation[top]) < m:
                    allocation[top].append(agent)
                    total_utility += util
                    allocated = True
                else:
                    i += 1
            else:
                allocation[top] = [agent]
                total_utility += util
                allocated = True
                
    return allocation, total_utility

def Graph(agents, allocation, available_timeslots):
    '''
    agents: This is the { i: agent( i, bed_times[i], sleep_times[i], fave_days[i]) for i in range(n)}
    allocation: This is a list A[t] where t is a timeslot and A[t] gives the list of agents currently in possession of 
    # timeslot t and want to trade 
    '''
    G = []
    # Since each agent only points to one other agent in the TTC graph, we can represent the graph as a single list G where 
    # each index i represents an agent, and G[i] represents the agent that it is pointing to
    for agent in list(agents.keys()):
        i = 0
        while agents[agent].pref_order[i][0] not in available_timeslots and i < len(agents[agent].pref_order):
            i += 1 
        G.append(agents[allocation[agents[agent].pref_order[i][0]]])

def fairness(agents, allocation):
    allocated_machine = {}
    #key, value = timeslot, list of people allocated to timeslot
    for k,v in allocation.items():
        for agent in v:
            allocated_machine[agent] = k
    total_fair = 0
    for agent in agents:
        if allocated_machine.get(agent):
            prefs = [f for f,s in agents[agent].pref_order]
            if prefs.index(allocated_machine[agent]) < 1:
                total_fair += 1
    return total_fair / n * 100



# simulate a week

def simulate(agents):
    num_weeks = 12

    # run RSD first
    print("***** Running RSD *****\n")
    total_total_utility = 0
    total_fairness = 0
    for week in range(num_weeks):
        allocation, total_utility = single_RSD(agents)
        print("Week", week + 1)
        print("\tTotal utility from RSD is:", total_utility)
        total_total_utility += total_utility
        f = fairness(agents, allocation)
        print("\tFairness from RSD is", fairness(agents, allocation), "%")
        total_fairness += f
    print("Total Utility from", num_weeks, "weeks:", total_total_utility)
    print("Average Fairness from", num_weeks, "weeks:", total_fairness/num_weeks, "%\n")

    # run TTC week
    print("***** Running TTC week *****\n")
    total_total_utility = 0
    total_fairness = 0
    for week in range(num_weeks):
        allocation, total_utility = single_RSD(agents)
        print("Week", week + 1)
        print("\tTotal utility from TTC week s:", total_utility)
        total_total_utility += total_utility
        f = fairness(agents, allocation)
        print("\tFairness from TTC week is", fairness(agents, allocation), "%")
        total_fairness += f
    print("Total Utility from", num_weeks, "weeks:", total_total_utility)
    print("Average Fairness from", num_weeks, "weeks:", total_fairness/num_weeks, "%\n")

    # run TTC day
    print("***** Running TTC Day *****\n")
    total_total_utility = 0
    total_fairness = 0
    for week in range(num_weeks):
        allocation, total_utility = single_RSD(agents)
        print("Week", week + 1)
        print("\tTotal utility from TTC day is:", total_utility)
        total_total_utility += total_utility
        f = fairness(agents, allocation)
        print("\tFairness from TTC day is", fairness(agents, allocation), "%")
        total_fairness += f
    print("Total Utility from", num_weeks, "weeks:", total_total_utility)
    print("Average Fairness from", num_weeks, "weeks:", total_fairness/num_weeks, "%\n")

    # run RSD/TTC combined
    print("***** Running RSD/TTC combined *****\n")
    total_total_utility = 0
    total_fairness = 0
    for week in range(num_weeks):
        allocation, total_utility = single_RSD(agents)
        print("Week", week + 1)
        print("\tTotal utility from RSD/TTC combined is:", total_utility)
        total_total_utility += total_utility
        f = fairness(agents, allocation)
        print("\tFairness from RSD/TTC combined is", fairness(agents, allocation), "%")
        total_fairness += f
    print("Total Utility from", num_weeks, "weeks:", total_total_utility)
    print("Average Fairness from", num_weeks, "weeks:", total_fairness/num_weeks, "%\n")


# iterate over each day of the week

# with small probability for each agent, their current allocaiton is released

# each agent now points to their top available preference

# run TTC mechanism

# if there is an available spot that is preferred then point to it,this will be for everybody, not just releasing people,
# but the total spots available will consist of the released spots + initially unallocated spots

simulate(agents)