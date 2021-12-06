#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Dec  4 16:19:11 2021

@author: alec
"""
import random
from agent_v3 import agent

# number of agents in the simulation
n = 100

# number of washer machines
m = 1

# randomize agent preferences REVISIT 
fave_days = random.choices(list(range(0,7,1)),k=n)
bed_times = random.choices([20,21,22,23,24,1,2,3],k=n)
sleep_times = random.choices([6,7,8,9],k=n)

# intialize agents
agents = { i: agent( i, bed_times[i], sleep_times[i], fave_days[i], 500) for i in range(n)}

# runs a single round of random serial dictatorship
def single_RSD(agents):
    
    # randomize the order
    order = list(agents.keys())
    random.shuffle(order)

    # dict of (time slot #, list of allocated agents)
    allocation = {}
    total_utility = 0
    remaining_timeslots = {i : True for i in range(0, 10800, 10)}
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
                    agents[agent].allocated_timeslot = top
                    remaining_timeslots.pop(top, None)
                    total_utility += util
                    allocated = True
                else:
                    i += 1
            else:
                allocation[top] = [agent]
                agents[agent].allocated_timeslot = top
                remaining_timeslots.pop(top, None)
                total_utility += util
                allocated = True

    return allocation, total_utility, remaining_timeslots


def unhappy_agents(agents, allocation):
    '''
    Input Parameters:
    agents: This is the { i: agent( i, bed_times[i], sleep_times[i], fave_days[i]) for i in range(n)}
    allocation: This is a list allocation[t] where t is a timeslot and allocation[t] gives the list of agents currently in 
    possession of timeslot t 

    Returns:
    agents_with_conflict: Agents who are unhappy with their current allocation due to last minute schedule conflict. Will participate in TTC
    available_timeslots: Timeslots available to be traded in the upcoming TTC run
    pre_ttc_allocation: This is a list pre_ttc_allocation[t] where t is a timeslot and pre_ttc_allocation[t] gives the 
    list of agents currently in possession of timeslot t and want to trade in the upcoming TTC
    '''
    prob_sched_conflict = 0.1
    agents_with_conflict = []
    available_timeslots = []
    ttc_allocation = {}
    real_agent_pre_ttc_allocation = {}
    # Flip allocation to agent --> allocated timeslot for easier processing
    #key, value = timeslot, list of people allocated to timeslot
    for k,v in allocation.items():
        for a in v:
            ttc_allocation[a] = k

    for a in list(agents.keys()):
        if random.random() <= prob_sched_conflict:
            agents[a].reorder_preferences(agents[a].allocated_timeslot)
            agents_with_conflict.append(agents[a])
            available_timeslots.append(agents[a].allocated_timeslot)
            real_agent_pre_ttc_allocation[a] = agents[a].allocated_timeslot
        # If the agent is happy with their current allocated timeslot, they will not participate in the TTC 
        else:
            ttc_allocation.pop(a)

    unallocated_timeslots = set(range(0, 10080, 10)).difference(set([agents[a].allocated_timeslot for a in agents]))
    dummy_id = n
    for timeslot in unallocated_timeslots:
        dummy_agent = agent(dummy_id, 0, 0, 0, 500)
        dummy_agent.allocated_timeslot = timeslot
        agents_with_conflict.append(dummy_agent)
        available_timeslots.append(timeslot)
        ttc_allocation[dummy_id] = timeslot
        dummy_id += 1

    # Flip it back to timeslot --> agents allocated to this timeslot
    pre_ttc_allocation = {}
    for a, timeslot in ttc_allocation.items():
        if timeslot in pre_ttc_allocation.keys():
            pre_ttc_allocation[timeslot].append(a)
        else:
            pre_ttc_allocation[timeslot] = [a]
    return agents_with_conflict, available_timeslots, pre_ttc_allocation, real_agent_pre_ttc_allocation


class TTC:
    def __init__(self, unhappy_agents, available_timeslots, pre_ttc_allocation, remaining_timeslots):
        self.unhappy_agents = unhappy_agents
        self.available_timeslots = available_timeslots
        self.pre_ttc_allocation = pre_ttc_allocation
        self.remaining_timeslots = remaining_timeslots
        self.G = None

    def create_unhappy_graph(self):
        '''
        Input Parameters:
        unhappy_agents: This is the unhappy_agents(agents, allocation)
        available_timeslots: Timeslots available to be traded in the upcoming TTC run
        pre_ttc_allocation: This is a list pre_ttc_allocation[t] where t is a timeslot and pre_ttc_allocation[t] gives the 
        list of agents currently in possession of timeslot t and want to trade in the upcoming TTC

        Returns:
        G: An adjacency list representing a directed graph to be used for TTC. Each index i represents an agent, and G[i] 
        represents a list of agents that it is pointing to (multiple agents may have the same timeslot, since there can be 
        more than one laundry machine). The first lists in G are all the real agents. The second half of the lists are dummy 
        agents that hold untaken slots.
        '''
        G = {}
        all_real_unhappy_agents = [a.id for a in self.unhappy_agents if a.id < n]
        for a in self.unhappy_agents:
            if a.id < n:
                i = 0
                while a.pref_order[i][0] not in self.available_timeslots and i < len(a.pref_order):
                    i += 1
                G[a.id] = self.pre_ttc_allocation[a.pref_order[i][0]]
            else:
                G[a.id] = all_real_unhappy_agents

        self.G = G
        self.visited = [False] * len(self.G)
        return G

    def start_vertex(self):
        # We only need to start finding cycles from vertices that represent actual agents
        for a in self.unhappy_agents:
            # If this vertex has not been removed
            if self.G.get(a.id) and a.id < n:
                return a.id
        return -1

    def add_edge(self, source, target):
        self.G[source] = target

    def delete_vertex(self, v):
        # explicitly deleting v would cause problems with keeping track of which agent corresponds to which vertex
        # We will simply empty the list G[v] and delete v from all other vertex lists such that v is essentially a standalone vertex         
        self.G.pop(v, None)
        for key,val in self.G.items():
            if v in val:
                self.G[key].remove(v)

    def find_cycle(self):
        visited = []
        v = self.start_vertex()
        if v != -1:
            path = [v]
            while v not in visited:
                visited.append(v)
                # Each vertex only points to one other vertex, so just visit that vertex
                v = self.G[v][0]
                path.append(v)
            # the last vertex in cycle is when we take the backward edge, so we need to cut it off there
            if len(path) > 1:
                cycle = path[path.index(v):]
                return cycle
            else:
                return []
        return []

    def check_TTC_complete(self):
        remaining_vertices = list(self.G.keys()) 
        for v in remaining_vertices:
            if v < n:
                return False
        return True

    def single_TTC(self):
        pre_ttc_allocation = {}
        post_ttc_allocation = {}
        remaining_vertices = {}
        # Flip allocation to agent --> allocated timeslot for easier processing
        for k,v in self.pre_ttc_allocation.items():
            for agent in v:
                pre_ttc_allocation[agent] = k
                remaining_vertices[agent] = k

        self.create_unhappy_graph()

        while not self.check_TTC_complete():
            cycle = self.find_cycle()
            # assign agents in the cycle their house
            for i in range(len(cycle)-1):
                pointed_agent = self.G[cycle[i]][0]
                if cycle[i] < n:
                    post_ttc_allocation[cycle[i]] = pre_ttc_allocation[pointed_agent]

                remaining_vertices.pop(cycle[i], None)
            for i in range(len(cycle)-1):
                self.delete_vertex(cycle[i])

            for a in self.unhappy_agents:
                if self.G.get(a.id, None) is not None and self.G[a.id] == [] and remaining_vertices.get(a.id, None) is not None:
                    i = 0
                    while a.pref_order[i][0] not in list(remaining_vertices.values()) and i < len(a.pref_order):
                        i += 1 
                    self.add_edge(a.id, self.pre_ttc_allocation[a.pref_order[i][0]])
                    if self.G[a.id] == [a.id]:
                        if a.id < n:
                            post_ttc_allocation[a.id] = pre_ttc_allocation[a.id]
                        self.delete_vertex(a.id)

        return post_ttc_allocation


def fairness(agents, allocation, top):
    total_fair = 0
    for agent in agents:
        if allocation.get(agent.id):
            prefs = [f for f,s in agent.pref_order]
            if prefs.index(allocation[agent.id]) < top:
                total_fair += 1
    return total_fair / n * 100


'''def fairness(agents, allocation, top):
    allocated_machine = {}
    #key, value = timeslot, list of people allocated to timeslot
    for k,v in allocation.items():
        for agent in v:
            allocated_machine[agent] = k
    total_fair = 0
    for agent in agents:
        if allocated_machine.get(agent.id):
            prefs = [f for f,s in agents[agent.id].pref_order]
            if prefs.index(allocated_machine[agent]) < top:
                total_fair += 1
    return total_fair / n * 100'''
# simulate a week

def simulate(agents):
    num_weeks = 12
    mechanisms = ['RSD', 'TTC', 'RSD & TTC', 'TTC & TTC']
    for m in mechanisms:
        print("***** Running", m, "*****\n")
        total_total_utility = 0
        total_fairness = 0
        total_top_choice = 0
        for week in range(num_weeks):
            allocation, total_utility, remaining_timeslots = single_RSD(agents)
            print("Week", week + 1)
            print("\tTotal utility from", m, "is:", total_utility)
            total_total_utility += total_utility
            f1 = fairness(agents, allocation, 3)
            print("\tFairness from", m, "is", fairness(agents, allocation, 3), "%")
            total_fairness += f1
            f2 = fairness(agents, allocation, 1)
            print("\tTop Choice from", m, "is", fairness(agents, allocation, 1), "%")
            total_top_choice += f2
        print("Total Utility from", num_weeks, "weeks:", total_total_utility)
        print("Average Fairness from", num_weeks, "weeks:", total_fairness/num_weeks, "%\n")
        print("Top Choice from", num_weeks, "weeks:", total_top_choice/num_weeks, "%\n")


# iterate over each day of the week

# with small probability for each agent, their current allocaiton is released

# each agent now points to their top available preference

# run TTC mechanism

# if there is an available spot that is preferred then point to it,this will be for everybody, not just releasing people,
# but the total spots available will consist of the released spots + initially unallocated spots

#simulate(agents)

'''allocation, total_utility, remaining_timeslots = single_RSD(agents)
print(remaining_timeslots)
agents_with_conflict, available_timeslots, pre_ttc_allocation = unhappy_agents(agents, allocation)
print(available_timeslots)
print(final_ttc_allocation)

print()'''

allocation, total_utility, remaining_timeslots = single_RSD(agents)
agents_with_conflict, available_timeslots, pre_ttc_allocation, real_agent_pre_ttc_allocation = unhappy_agents(agents, allocation)
TTC_mechanism = TTC(agents_with_conflict, available_timeslots, pre_ttc_allocation, remaining_timeslots)
post_ttc_allocation = TTC_mechanism.single_TTC()

print(real_agent_pre_ttc_allocation)
print(post_ttc_allocation)
all_real_unhappy_agents_ids = [a.id for a in agents_with_conflict if a.id < n]
all_real_unhappy_agents = [a for a in agents_with_conflict if a.id < n]

print(all_real_unhappy_agents_ids)
print(fairness(all_real_unhappy_agents, real_agent_pre_ttc_allocation, 5))
print(fairness(all_real_unhappy_agents, post_ttc_allocation, 5))
