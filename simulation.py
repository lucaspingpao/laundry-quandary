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
m = 1

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
    free_timeslots = {i : True for i in range(10800)}
    # iterate over agents in order
    for agent in list(order):
        prefs = agents[agent].pref_order        
        for i in range(len(prefs)):
            # current top preference
            top = prefs[i][0]
            util = prefs[i][1]
            
            # check if their current top preference is still available
            if top in allocation.keys():
                if len(allocation[top]) < m:
                    allocation[top] = agent
                    agents[agent].allocated_timeslot = top
                    free_timeslots.pop(top, None)
                    total_utility += util
                    allocated = True
            else:
                allocation[top] = [agent]
                agents[agent].allocated_timeslot = top
                free_timeslots.pop(top, None)
                total_utility += util
                allocated = True

    agent_timeslot_allocation = {}
    # Flip allocation to agent --> allocated timeslot for easier processing
    #key, value = timeslot, list of people allocated to timeslot
    for timeslot, agents in allocation.items():
        for agent in agents:
            agent_timeslot_allocation[agent] = timeslot
                
    return agent_timeslot_allocation, total_utility, free_timeslots


def unhappy_agents(agents, allocation, free_timeslots):
    '''
    Input Parameters:
    agents: This is the { i: agent( i, bed_times[i], sleep_times[i], fave_days[i]) for i in range(n)}
    allocation: This is a list allocation[a] where a is an agent and allocation[a] gives the timeslot currently in a's possession

    Returns:
    agents_with_conflict: Agents who are unhappy with their current allocation due to last minute schedule conflict. Will participate in TTC
    available_timeslots: Timeslots available to be traded in the upcoming TTC run
    final_ttc_allocation: This is a list final_ttc_allocation[t] where t is a timeslot and final_ttc_allocation[t] gives the 
    list of agents currently in possession of timeslot t and want to trade in the upcoming TTC
    '''
    prob_sched_conflict = 0.1
    agents_with_conflict = {}
    available_timeslots = {}
    ttc_allocation = allocation

    for agent in list(agents.keys()):
        if random.random() <= prob_sched_conflict:
            agents[agent].reorder_preferences(agents[agent].allocated_timeslot)
            agents_with_conflict[agent] = agents[agent]
            available_timeslots[agents[agent].allocated_timeslot] = True
        # If the agent is happy with their current allocated timeslot, they will not participate in the TTC 
        else:
            ttc_allocation.pop(agent)

    # Add dummy agents to the ttc_allocation
    for dummy_id, t in enumerate(list(free_timeslots.keys())):
        ttc_allocation[n+dummy_id] = free_timeslots[t]
        available_timeslots[t] = True

    # Flip it back to timeslot --> agents allocated to this timeslot
    final_ttc_allocation = {}
    for a, timeslot in ttc_allocation.items():
        if timeslot in final_ttc_allocation.keys():
            final_ttc_allocation[timeslot].append(a)
        else:
            final_ttc_allocation[timeslot] = [a]
    return agents_with_conflict, available_timeslots, final_ttc_allocation

class TTC:
    def __init__(self, all_agents, overall_allocation, unhappy_agents, available_timeslots, final_ttc_allocation, free_timeslots):
        self.overall_allocation = overall_allocation
        self.all_agents = all_agents
        self.unhappy_agents = unhappy_agents
        self.available_timeslots = available_timeslots
        self.final_ttc_allocation = final_ttc_allocation
        self.free_timeslots = free_timeslots
        self.dummy_agents = zip(range(len(list(free_timeslots.keys()))), list(free_timeslots.keys()))
        self.G = None

    def create_unhappy_graph(self):
        '''
        Input Parameters:
        unhappy_agents: This is the unhappy_agents(agents, allocation)
        available_timeslots: Timeslots available to be traded in the upcoming TTC run
        final_ttc_allocation: This is a list final_ttc_allocation[t] where t is a timeslot and final_ttc_allocation[t] gives the 
        list of agents currently in possession of timeslot t and want to trade in the upcoming TTC

        Returns:
        G: An adjacency list representing a directed graph to be used for TTC. Each index i represents an agent, and G[i] 
        represents a list of agents that it is pointing to (multiple agents may have the same timeslot, since there can be 
        more than one laundry machine). The first lists in G are all the real agents. The second half of the lists are dummy 
        agents that hold untaken slots.
        '''
        G = []
        for agent in list(self.unhappy_agents.keys()):
            i = 0
            while self.available_timeslots.get(self.unhappy_agents[agent].pref_order[i][0], None) is None and i < len(self.unhappy_agents[agent].pref_order):
                i += 1 
            G.append(self.final_ttc_allocation[self.unhappy_agents[agent].pref_order[i][0]])

        # When accessing the timeslot of the dummy agents, use - len(list(self.unhappy_agents.keys()))
        for free_timeslot in list(self.free_timeslots.keys()):
            G.append(list(self.unhappy_agents.keys()))

        self.G = G
        self.visited = [False] * len(self.G)
        return G

    def start_vertex(self):
        # We only need to start finding cycles from vertices that represent actual agents
        for v in len(self.unhappy_agents):
            # If this vertex has not been removed
            if len(self.G[v]) > 0:
                return v

    def add_edge(self, source, target):
        self.G[source].append(target)

    def delete_vertex(self, v):
        # explicitly deleting v would cause problems with keeping track of which agent corresponds to which vertex
        # We will simply empty the list G[v] and delete v from all other vertex lists such that v is essentially a standalone vertex         
        self.G[v] = []
        for i in len(self.G):
            if v in self.G[i]:
                self.G[i].remove(v)

    def find_cycle(self):
        visited = set()
        v = self.start_vertex()
        path = [v]
        while v not in visited:
            visited.add(v)
            # Each vertex only points to one other vertex, so just visit that vertex
            v = self.G[v][0]
            path.append(v)
        # the last vertex in cycle is when we take the backward edge, so we need to cut it off there
        cycle = path[path.index(v):]
        return cycle

    def single_TTC(self):
        '''
        Returns:
        post_ttc_allocation: New allocation for unhappy agents after TTC, post_ttc_allocation[a] gives timeslot allocated to a
        (Note) The indices for post_ttc_allocation are in range(len(self.unhappy_agents)) instead of their actual indices in 
        all the agents, so this needs to be converted back using self.unhappy_agents
        '''
        pre_ttc_allocation = {}
        post_ttc_allocation = {}
        remaining_vertices = {}
        # Flip allocation to agent --> allocated timeslot for easier processing
        for k,v in self.final_ttc_allocation.items():
            for agent in v:
                pre_ttc_allocation[agent] = k
                remaining_vertices[agent] = k

        self.create_unhappy_graph()
        empty = []
        for i in range(len(list(self.unhappy_agents.keys()))):
            empty.append([])

        while self.G[:len(list(self.unhappy_agents.keys()))] != empty:
            cycle = self.find_cycle()
            # assign agents in the cycle their house
            for i in range(len(cycle)-1):
                pointed_agent = self.G[cycle[i]][0]
                post_ttc_allocation[cycle[i]] = pre_ttc_allocation[pointed_agent]
                self.G.delete_vertex(cycle[i])
                remaining_vertices.pop(cycle[i], None)

            for agent in self.unhappy_agents:
                if self.G[agent] == [] and remaining_vertices.get(agent, None) is not None:
                    i = 0
                    while self.unhappy_agents[agent].pref_order[i][0] not in list(remaining_vertices.values()) and i < len(self.unhappy_agents[agent].pref_order):
                        i += 1 
                    self.G.add_edge(agent, self.final_ttc_allocation[self.unhappy_agents[agent].pref_order[i][0]])
        print(post_ttc_allocation)

        #overall_post_ttc_alloc = self.overall_allocation
        #for agent_id, unhappy_agent in enumerate(list(self.unhappy_agents.keys())):
        #    overall_post_ttc_alloc[unhappy_agent] = post_ttc_allocation[]

        return post_ttc_allocation



def fairness(agents, allocation):
    total_fair = 0
    for agent in agents:
        if allocation.get(agent):
            prefs = [f for f,s in agents[agent].pref_order]
            if prefs.index(allocation[agent]) < 50:
                total_fair += 1
    return 100 * total_fair / n 



# simulate a week

def simulate(agents):
    # run RSD first
    agent_timeslot_allocation, total_utility, free_timeslots = single_RSD(agents)
    print(agent_timeslot_allocation)
    print("Total utility from RSD is:", total_utility)
    print("Fairness is", fairness(agents, agent_timeslot_allocation), "%")



# iterate over each day of the week

# with small probability for each agent, their current allocaiton is released

# each agent now points to their top available preference

# run TTC mechanism

# if there is an available spot that is preferred then point to it,this will be for everybody, not just releasing people,
# but the total spots available will consist of the released spots + initially unallocated spots

simulate(agents)