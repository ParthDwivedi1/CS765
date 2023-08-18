import argparse
from queue import PriorityQueue
import numpy as np


# Creates a random graph

def graph_creation(peers):
    
    degree=[0 for i in range(peers)] # Keeping a count of degree of each vertex

    edges=[[] for i in range(peers)] # Actual edges in the graph
    
    saturated=[] # Nodes that have achieved their maximum degree
    
    for i in range(peers):
        num=np.random.choice([4,5,6,7,8]) # Choose the degree of the current node randomly
        
        if num<=degree[i]:
            # If current degree is more than the choice, then skip
            continue
        
        # From all nodes having index greater than i, we remove the saturated nodes to get potential neighbors
        potential_neighbors=list(set(range(i+1,peers))-set(saturated))
        
        # From the potential neighbors choose the required number of neighbors, or all of them if not enough neighbors are available
        
        neighbors = np.random.choice(potential_neighbors,min(len(potential_neighbors),num-degree[i]),replace=False)
        
        for ele in neighbors:
            
            # Add edge and update degree and saturated nodes
            edges[i].append(ele)
            edges[ele].append(i)
            degree[i]+=1
            degree[ele]+=1
            if(degree[ele]==8):
                saturated.append(ele)
            
    return edges

# Recursive Depth First Search

def dfs(edges,root,visited):
    visited[root]=True
    
    for x in edges[root]:
        if visited[x]:
            continue
        dfs(edges,x,visited)

# Checks if graph is connected using DFS

def graph_connected(edges,peers):
    visited=[False for i in range(peers)]
    
    dfs(edges,0,visited)
    
    # print(maxi,mini)
    for ele in visited:
        if(not ele):
            return ele
    
    return True