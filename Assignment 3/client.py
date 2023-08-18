import json
from web3 import Web3
import uuid
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
from collections import deque

mean=1.0

#connect to the local ethereum blockchain
provider = Web3.HTTPProvider('http://127.0.0.1:8545')
w3 = Web3(provider)
#check if ethereum is connected
print(w3.is_connected())

#replace the address with your contract address (!very important)
deployed_contract_address = '0xb1f037fed74c3FdD38B54631c8C1AC229af34204'

#path of the contract json file. edit it with your contract json file
compiled_contract_path ="build/contracts/Payment.json"
with open(compiled_contract_path) as file:
    contract_json = json.load(file)
    contract_abi = contract_json['abi']
contract = w3.eth.contract(address = deployed_contract_address, abi = contract_abi)

print(contract)

g=open('debug.txt','w')

'''
#Calling a contract function createAcc(uint,uint,uint)
txn_receipt = contract.functions.createAcc(1, 2, 5).transact({'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':2409638})
txn_receipt_json = json.loads(w3.to_json(txn_receipt))
print(txn_receipt_json) # print transaction hash

# print block info that has the transaction)
print(w3.eth.get_transaction(txn_receipt_json)) 

#Call a read only contract function by replacing transact() with call()

'''

#Add your Code here

# Function to register a given number of users

def registerUsers(n):
    
    # Call the register function for all users,
    # having name as a random uuid
    for i in range(1,n+1):
        txn_receipt = contract.functions.registerUser(i,str(uuid.uuid4())).transact({'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':2409638,'gas price':0})
        txn_receipt = w3.eth.get_transaction_receipt(txn_receipt)
        event_logs=contract.events.UserRegister().process_receipt(txn_receipt)
        # print(event_logs)
        # Debug statement

# Function to create accounts according to the edges in the graph
def createAccounts(graph,edges):
    for edge in graph.edges():
        bal=(int)(np.random.exponential(scale=mean))
        
        # Ensuring that balance is distributed equally between the two nodes
        edges[edge[0]+1].append([edge[1]+1,bal//2,bal-bal//2])
        edges[edge[1]+1].append([edge[0]+1,bal-bal//2,bal//2])
        
        txn_receipt = contract.functions.createAcc(edge[0]+1,edge[1]+1,bal).transact({'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':2409638,'gas price':0})
        txn_receipt = w3.eth.get_transaction_receipt(txn_receipt)
        event_logs=contract.events.CreateAccount().process_receipt(txn_receipt)
        # print(event_logs)
        # Debug statement

        
# Function to process the transfer of money from one node to the other

def process_transfer(edges,st,end):
    
    # Creating a deque for BFS
    sto=deque()
    
    sto.append(st)
    
    # Visited array that stores whether a node has been visited or not for BFS
    visited=[False for i in range(len(edges))]
    # Maintaining the parent of each node to backtrack after BFS
    parent=[0 for i in range(len(edges))]
    
    visited[st]=True
    parent[st]=st
    
    #Starting BFS
       
    while(len(sto)>0):
        root=sto.popleft()
        
        for ele in edges[root]:
            
            # Only considering nodes that haven't been visited
            # and that have a balance greater than 0
            if(ele[1]<=0 or visited[ele[0]]):
                continue
            visited[ele[0]]=True
            parent[ele[0]]=root
            sto.append(ele[0])
        
        # If parent has been visited, break
        if(parent[end]!=0):
            break
    
    # If parent has not been visited, stop
    
    if(parent[end]==0):
        # print("FAILED\n\n\n")
        # Debug statement
        return 0;
    
    curr=end
    # Debug statements
    
    g.write(str(edges))
    g.write("\n")
    g.write("HEY"+str(st)+str(end)+"\n")
    
    # Backtrack, while sending amount along each node
    # till the start node is reached
    
    while(curr!=st):
        g.write(str(curr)+str(parent[curr])+"\n")
        
        # Sending amount along the edge
        txn_receipt = contract.functions.sendAmount(parent[curr],curr,1).transact({'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':2409638,'gas price':0})
        txn_receipt = w3.eth.get_transaction_receipt(txn_receipt)
        event_logs=contract.events.AmountSend().process_receipt(txn_receipt)
        # Debug statement
        g.write(str(event_logs))
        
        # Updating the graph here in the python file as well
        for ele in edges[curr]:
            if(ele[0]==parent[curr]):
                ele[1]+=1
                ele[2]-=1;
                break
                
        for ele in edges[parent[curr]]:
            if(ele[0]==curr):
                ele[1]-=1
                ele[2]+=1
                break
        
        # Moving up the chain to the parent of the current node
        curr=parent[curr]
    
    return 1

#Function to delete all accounts

def removeAccounts(graph):
    
    #Remove all edges in the graph one by one
    
    for edge in graph.edges():
        txn_receipt = contract.functions.closeAccount(edge[0]+1,edge[1]+1).transact({'txType':"0x3", 'from':w3.eth.accounts[0], 'gas':2409638,'gas price':0})
        txn_receipt = w3.eth.get_transaction_receipt(txn_receipt)
        event_logs=contract.events.CloseAccount().process_receipt(txn_receipt)
        # print(event_logs)
        # Debug Statements

        
if __name__=='__main__':
    
    # Fixing the number of users
    num_users=100
    
    # Creating the edges array
    edges=[[] for i in range(num_users+1)]
    
    #Registering the users
    registerUsers(num_users);
    
    print("Registered!")
    
    # Creating a graph according to power law distribution
    
    graph = nx.powerlaw_cluster_graph(num_users,3,0.3)
    
    # Checking if connected, and keep creating new graphs till we get a connected one
    while(not nx.is_connected(graph)):
        graph = nx.powerlaw_cluster_graph(num_users,3,0.3)
    
    #Create accounts according to this graph
    createAccounts(graph,edges)
    print("Created Accounts")
    
    # Fixing the number of transactions
    num_transactions = 1000
    
    succ=0
    tot=0
    
    ratios=[]
    
    for i in range(num_transactions):
        
        if(i!=0 and (i)%100==0):
            # At every multiple of 100, print successful vs total transactions
            print(succ,tot,succ/tot)
            ratios.append(succ/tot)
        
        st=1
        end=1
        
        # Choosing two random nodes for the transaction, making sure that they are not the same node
        while(st==end):
            st=np.random.randint(1,num_users)
            end=np.random.randint(1,num_users) 
            
        succ+=process_transfer(edges,st,end) 
        tot+=1
        
    print(succ,tot,succ/tot)
    ratios.append(succ/tot)
    
    x=[(i*100) for i in range(1,num_transactions//100+1)]
    
    plt.plot(x,ratios)
    plt.xlabel("Total number of Transactions")
    plt.ylabel("Ratio of Successful to Total transactions")
    plt.show()
    
    # Finally remove all edges from the graph
    
    removeAccounts(graph)
    print("Removed all accounts")