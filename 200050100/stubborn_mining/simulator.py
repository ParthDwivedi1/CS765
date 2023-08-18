import argparse
from queue import PriorityQueue
import numpy as np
import sys
from graph import *
from structures import Block , Peer , Transaction
import uuid
from utility import *
from visualize import *
from copy import deepcopy
import faulthandler

# All sizes in kiloBITS, speeds in Kilobits per second, time in milliseconds

faulthandler.enable()
sys.setrecursionlimit(10**6)

if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--peers", help='number of peers',type=int)
    parser.add_argument("--slow", help='percentage of slow nodes',type=float)
    parser.add_argument("--lowcpu", help='percentage of low CPU nodes',type=float)
    parser.add_argument("--meantransactiontime", help='mean time between arrival of transactions in ms',type=float)
    parser.add_argument("--meanblocktime", help='mean time between arrival of blocks in ms',type=float)
    parser.add_argument("--attackerpower", help='hashing power with the attacker',type=float)
    parser.add_argument("--attackerspeed", help='whether the attacker is a fast node (1) or a slow node (0)',type=bool)
    parser.add_argument("--attackerconnections", help='percentage of nodes the attacker is connected to',type=float)
    
    
    args=parser.parse_args()
    peers=args.peers #Number of peers
    slow=args.slow # Percentage of slow peers
    lowcpu=args.lowcpu # Percentage of lowcpu peers
    meantransactiontime=args.meantransactiontime # Mean transaction time in ms
    meanblocktime=args.meanblocktime # Mean block arrival time in ms
    attackerpower=args.attackerpower # Hashing Power with the attacker
    attackerspeed=args.attackerspeed # Whether the attacker is fast or slow
    attackerconnections=args.attackerconnections # Percentage of nodes to which the attacker is connected to

    if((args.peers is None) or (args.slow is None) or (args.lowcpu is None) or (args.meanblocktime is None) or (args.meantransactiontime is None) or (args.attackerpower is None) or (args.attackerspeed is None) or (args.attackerconnections is None)):
        print("usage: python simulator.py [--peers PEERS] [--slow SLOW] [--lowcpu LOWCPU] [--meantransactiontime MEANTRANSACTIONTIME] [--meanblocktime MEANBLOCKTIME]")
        exit(0)
        
    # Defined format of tasks below
    
    #Priority Queue sorts tasks on basis of increasing order of first element, i.e. time
    
    task_list = PriorityQueue() # [time , peer_ID , type_of_action          , ... ]
                                # [                 'received_block'        , received_from, Block ]
                                # [                 'received_transaction'  , received_from , Transaction ]
                                # [                 'generate_block'        , Block ]
                                # [                 'generate_transaction'  , Transaction ]
    
    
    num_low =(int)((peers-1)*lowcpu/100) #Number of nodes with low cpu capabilities
                                
    low_hash=1.0/(num_low+(peers-1-num_low)*10)
    high_hash=10.0/(num_low+(peers-1-num_low)*10)   
    
    low_hash*=1-(attackerpower/100)
    high_hash*=1-(attackerpower/100)
    
    #Hashing power defined above to ensure high cpu nodes have 10 times the power of low cpu nodes
     
    peer_list = [Peer(i,'fast','highcpu',high_hash) for i in range(peers)]
    
    #Assigning slow nodes
    
    num =(int)((peers-1)*slow/100)
    ele = np.random.choice(range(1,peers),num,replace=False) # Choosing a random subset of elements and assigning them as slow 
    
    for i in ele:
        peer_list[i].speed='slow'
    
    #Assigning lowcpu nodes
    
    ele = np.random.choice(range(1,(peers)),num_low,replace=False) # Choosing a random subset of elements and assigning them as lowcpu
    
    for i in ele:
        peer_list[i].power='lowcpu'
        peer_list[i].hashingpower=low_hash
    
    # Giving parameters for the attacker node (considered to have Peer ID 0)
    
    # Setting attacker speed (whether it is a slow or fast node)
    if attackerspeed:
        peer_list[0].speed='fast'
    else:
        peer_list[0].speed='slow'
        
    # Assigning hashing power to the attacker node
    
    peer_list[0].hashingpower=attackerpower/100
    
    # Connecting the attacker to neighbors
    # Number of neighbors calculated on attackerconnections parameter
    
    num_neigh=(int)((peers-1)*(attackerconnections)/100)
    ele = np.random.choice(range(1,peers),num_neigh,replace=False)
    
    for i in ele:
        peer_list[0].neighbors.append(i)
        peer_list[i].neighbors.append(0)
    
    # Generating the original genesis block
    
    # Giving all nodes a balance of MININGFEE coins ( so that transactions can be initiated)
    
    transactions=[]
    for i in range(peers):
        base=Transaction(-1,i,MININGFEE,8000,uuid.uuid4())
        transactions.append(base)
        
    balances = [MININGFEE for i in range(peers)]
    genesis_block = Block(-1,0,-1,-1,transactions,0,0,balances)
    
    for i in range(peers):
        peer_list[i].received_blocks.append(genesis_block)
            
    # Graph Creation

    edges=graph_creation(peers)
    while(not graph_connected(edges,peers)):
        edges=graph_creation(peers)
        
        
    for i in range(peers):
        peer_list[i].neighbors=edges[i]
        
    # Setting speed of light propagation delay
    
    rho = np.random.uniform(10,500)  
    
    # Initializing the task list with transactions and blocks for each node
    
    for i in range(peers):
        # Need a gen_transation for each node to kickstart the transaction_generation process
        newtask=transaction_generation(peer_list[i],find_mining_block(peer_list[i]),meantransactiontime,0)
        task_list.put(newtask)
        print(newtask)
        
        # Need a gen_block for each node to kickstart the block_generation process
        newtask = block_generation(peer_list[i],meanblocktime,0)
        task_list.put(newtask)
        dump(newtask[3])
        print(newtask)
        
    count=0 # Determining point till which to run simulation
    
    print("--------START------------")
    
    lasttime=0
    
    while((not task_list.empty()) and (count<=10000) ):
        
        # Get earliest scheduled task in task list
        
        if count%10000==0:
            sys.stderr.write(str(count)+"\n")
            sys.stderr.flush()
                             
        
        task=task_list.get()
        print(task)
        
        lasttime=task[0]
        
        if(task[2] == 'received_block'):
            print("Block ID:", task[4].blk_id)
        elif(task[2] == 'received_transaction'):
            print("Transaction ID:",task[4].transaction_id)
        elif(task[2] == 'gen_block'):
            print("Block ID:",task[3].blk_id)
        else:
            print("Transaction ID:",task[3].transaction_id)
        
        count+=1 # Incrementing count
        
        if task[2] == 'received_block':
            
            #If block already reached, skip
            if find_block_depth(task[4].blk_id,peer_list[task[1]]) != -1:
                continue
            
            # If the attacker finds a block generated by itself, then it checks if
            # it is the block with the maximum depth among blocks generated by itself
            # if not, then the block is dropped. This stops the attacker from branching 
            # out on from its own chain
            
            if(peer_list[task[1]].id==0 and task[4].miner_id==0):
                if(task[4].depth<=find_own_max_depth(peer_list[task[1]])):
                    continue
            
            # Creating copy of block which will be updated
            block = Block(task[4].prev_blk_id,task[4].blk_id,task[4].miner_id,task[1],task[4].transactions,task[4].depth,task[0],task[4].balances)
            
            # Finding the depth of the parent block
            parent_depth = find_block_depth(block.prev_blk_id,peer_list[task[1]])
            
            #If no longer longest chain, drop own block
            
            if(block.miner_id==peer_list[task[1]].id):
                if(parent_depth!=peer_list[task[1]].max_depth):
                    if(peer_list[task[1]].id!=0):
                        continue
                    elif (peer_list[task[1]].attacker_lead==0):
                        continue
                        
            # If parent does not exist, cache block
            
            if parent_depth == -1:
                
                # Making a copy since we should not modify the original block and then appending to cache
                taskcopy = task.copy()
                taskcopy[4]=block
            
                # Adding a received block in cache only once
                if not exists_in_cache(block.blk_id,peer_list[task[1]]):
                    peer_list[task[1]].cacheBlock.append(taskcopy)

                continue
                    
            # Updating depth of block
            block.depth=parent_depth+1
            
            # Validate transactions of block and update left_transactions of Peer
            if(validate(block,peer_list[task[1]])):
                
                # On successful validation proceed, updation of node parameters is done below
                # If not, something has gone wrong and break the loop itself
                
                assert(block.owner==task[1])
            else:
                dump(block)
                print("Validation failed")
                break
            
            # Printing for debugging
            
            dump(block)
            
            # Broadcast to neighbors, except where it is received from
            # Broadcast only if not the attacker node or if it is the attacker node 
            # and block generated by itself
            # This is to be done only if the node is honest
            
            if(peer_list[task[1]].id!=0):
                peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,block.depth)
                peer_list[task[1]].received_blocks.append(block)
                
                for adjacent in peer_list[task[1]].neighbors:
                    if adjacent == task[3]:
                        continue
                    ntask = broadcast(task,peer_list[task[1]],peer_list[adjacent],rho)
                    task_list.put(ntask)
                    print("Added only:- ",ntask)
                    
            elif (task[4].miner_id!=0):
                
                # If attacker node receives a block not mined by itself
                # First, it updates its max_depth and list of received blocks
                # Then, it takes actions based on its lead over the honest chain
                
                peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,block.depth)
                peer_list[task[1]].received_blocks.append(block)
                
                if peer_list[task[1]].attacker_lead>=2:
                    
                    # If attacker lead is greater than or equal to 2,
                    # the attacker node, broadcasts exactly one node,
                    # keeping the rest of the chain secret.
                    
                    # Obviously it does not broadcast the honest node received
                    
                    # Broadcasting the secret node to neighbors
                    for adjacent in peer_list[task[1]].neighbors:
                        if adjacent == task[3]:
                            continue
                        peer_list[task[1]].secret_chain[0][0]=task[0]
                        ntask = broadcast(peer_list[task[1]].secret_chain[0],peer_list[task[1]],peer_list[adjacent],rho)
                        task_list.put(ntask)
                        print("Added only:- ",ntask)
                    
                    # The attacker lead is updated
                    peer_list[task[1]].attacker_lead-=1

                    # Added the secret block to list of received blocks
                    peer_list[task[1]].received_blocks.append(peer_list[task[1]].secret_chain[0][4])    
                    
                    # Updated the max_depth
                    peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,peer_list[task[1]].secret_chain[0][4].depth)                         
                    
                    # Removed the block from the secret chain
                    peer_list[task[1]].secret_chain=peer_list[task[1]].secret_chain[1:]

                elif peer_list[task[1]].attacker_lead==1:
                    
                    # If lead is of only one node, just broadcast the secret block
                    
                    for adjacent in peer_list[task[1]].neighbors:
                        if adjacent == task[3]:
                            continue
                        peer_list[task[1]].secret_chain[0][0]=task[0]
                        ntask = broadcast(peer_list[task[1]].secret_chain[0],peer_list[task[1]],peer_list[adjacent],rho)
                        task_list.put(ntask)
                        print("Added only:- ",ntask)

                    # Updating attacker lead
                    peer_list[task[1]].attacker_lead=0
                    # Added secret block to list of received blocks
                    peer_list[task[1]].received_blocks.append(peer_list[task[1]].secret_chain[0][4])
                    
                    # Updated the max_depth
                    peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,peer_list[task[1]].secret_chain[0][4].depth)
                    
                    # Empty the secret_chain of the attacker node
                    peer_list[task[1]].secret_chain=[]
            else:
                
                # Finally if the attacker node receives a block mined by itself
                # Then add this block (actually task) to the secret chain
                
                # Updating the value of task[4] so that the value of block depth
                # and other updated parameters are saved in the block
                
                task[4]=block
                peer_list[task[1]].secret_chain.append(task)
                peer_list[task[1]].attacker_lead+=1
                pass

            #Cached blocks can be added back now
            
            add_cache(task_list,peer_list,peer_list[task[1]],block,rho,task[0])

            #Schedule next block generation
            
            newtask = block_generation(peer_list[task[1]],meanblocktime,task[0])            
            print("Added only:- ",newtask)
            task_list.put(newtask)

            
            pass
        elif task[2] == 'received_transaction':
            
            #If already received, skip rest
            if exists_transaction(task[4].transaction_id,peer_list[task[1]]) != -1:
                continue
            
            # Create new transaction object for adding into list
            
            transaction = Transaction(task[4].start,task[4].destination,task[4].coins,task[4].size,task[4].transaction_id)
            
            # Append to received and left transactions
            peer_list[task[1]].received_transactions.append(transaction)
            
            if(not (exists_transaction_in_blocks(transaction,peer_list[task[1]]))):
                peer_list[task[1]].left_transactions.append(transaction)
            
            # Broadcast to neighbors except where it is received from
            for adjacent in peer_list[task[1]].neighbors:
                if adjacent == task[3]:
                    continue
                ntask = broadcast(task,peer_list[task[1]],peer_list[adjacent],rho)
                task_list.put(ntask)
                print("Added only:- ",ntask)
                
            pass
        elif task[2] == 'gen_block':
            
            #If not longest chain, stop mining
            
            if(peer_list[task[1]].id!=0):    
                if(task[3].depth!=peer_list[task[1]].max_depth+1):
                    continue
            else:
                if(task[3].depth!=peer_list[task[1]].max_depth+1 and (len(peer_list[task[1]].secret_chain)==0 or task[3].depth!=peer_list[task[1]].secret_chain[-1][4].depth+1)):
                    continue
                
            #Validate transaction before receiving, but not update, since updation is done in received_block
            if(validate_not_update(task[3],peer_list[task[1]])):
                pass
            else:
                
                print("Block should be dropped here! Happens in rare cases!")
                dump(task[3])
                continue
            
            #Add received_block task to use the received_block code
            block=deepcopy(task[3])
            newtask=([task[0],task[1],'received_block',task[1],block])
            print("Added only:- ",newtask)
            
            task_list.put(newtask)
                        
            pass
        elif task[2] == 'gen_transaction':
            
            # Add received_transaction task to use the received_transaction code
            
            newtask=[task[0],task[1],'received_transaction',task[1],task[3]]
            print("Added only:- ",newtask)
            
            task_list.put(newtask)
            
            # Add a new transaction generation task to keep the cycle going
            
            newtask=transaction_generation(peer_list[task[1]],find_mining_block(peer_list[task[1]]),meantransactiontime,task[0])
            print("Added only:- ",newtask)
            
            task_list.put(newtask)
            
        else:
            print("ERROR : INVALID TASK TYPE")
            break
        pass
    
    # When simulation ends, we allow the attacker node to broadcast its entire secret chain

    # Initializing an empty priority queue again
    task_list=PriorityQueue()
    co=0

    # For each block in secret_chain, add to task_list
    for task in peer_list[0].secret_chain:
        task[0]=lasttime+co
        co+=1
        task_list.put(task)
    
    # Keep broadcasting till every node has received nodes and no new tasks are being added
    while((not task_list.empty())):
        
        # Get earliest scheduled task in task list
        
        task=task_list.get()
        print(task)
        
        count+=1 # Incrementing count
        
        # All tasks will only received_block, hence no check here
        
        #If block already reached, skip
        if find_block_depth(task[4].blk_id,peer_list[task[1]]) != -1:
            continue
        
        # If the attacker finds a block generated by itself, then it checks if
        # it is the block with the maximum depth among blocks generated by itself
        # if not, then the block is dropped. This stops the attacker from branching 
        # out on from its own chain
        
        if(peer_list[task[1]].id==0 and task[4].miner_id==0):
            if(task[4].depth<=find_own_max_depth(peer_list[task[1]])):
                continue
        
        # Creating copy of block which will be updated
        block = Block(task[4].prev_blk_id,task[4].blk_id,task[4].miner_id,task[1],task[4].transactions,task[4].depth,task[0],task[4].balances)
        
        # Finding the depth of the parent block
        parent_depth = find_block_depth(block.prev_blk_id,peer_list[task[1]])
        
        #If no longer longest chain, drop own block
        
        if(block.miner_id==peer_list[task[1]].id):
            if(parent_depth!=peer_list[task[1]].max_depth):
                if(peer_list[task[1]].id!=0):
                    continue
                elif (peer_list[task[1]].attacker_lead==0):
                    continue
                    
        # If parent does not exist, cache block
        
        if parent_depth == -1:
            
            # Making a copy since we should not modify the original block and then appending to cache
            taskcopy = task.copy()
            taskcopy[4]=block
        
            # Adding a received block in cache only once
            if not exists_in_cache(block.blk_id,peer_list[task[1]]):
                peer_list[task[1]].cacheBlock.append(taskcopy)

            continue
                
        # Updating depth of block
        block.depth=parent_depth+1
        
        # Validate transactions of block and update left_transactions of Peer
        if(validate(block,peer_list[task[1]])):
            
            # On successful validation proceed, updation of node parameters is done below
            # If not, something has gone wrong and break the loop itself
            
            peer_list[task[1]].max_depth=max(peer_list[task[1]].max_depth,block.depth)
            peer_list[task[1]].received_blocks.append(block)
        
            assert(block.owner==task[1])
        else:
            dump(block)
            print("Validation failed")
            break
        
        # Broadcast to neighbors, except where it is received from
        # Broadcast only if not the attacker node or if it is the attacker node 
        # and block generated by itself
                    
        for adjacent in peer_list[task[1]].neighbors:
            if adjacent == task[3]:
                continue
            
            ntask = broadcast(task,peer_list[task[1]],peer_list[adjacent],rho)
            task_list.put(ntask)
            print("Added only:- ",ntask)
        # Cached blocks can be added back now
        
        add_cache(task_list,peer_list,peer_list[task[1]],block,rho,task[0])
        pass
        
        
# Finally printing out the received blocks of each of the peers in a separate file

g=open("Ratios.out",'w')

for i in range(peers):
    
    s = f"Peer{i}_Block_Details.out"
    f= open(s,'w')
    
    current=0
    maxi=-1
    
    tot2=0
    
    for block in peer_list[i].received_blocks:
        
        if(block.miner_id==0):
            tot2+=1        
        if(block.depth>maxi):
            current=block
            maxi=block.depth

    tot_0=0
    tot=0
    
    
    while(current.blk_id!=0):
        if(current.miner_id==0):
            tot_0+=1
        tot+=1
        for blk in peer_list[i].received_blocks:
            if(blk.blk_id==current.prev_blk_id):
                current=blk
                break
    
    tot+=1

    dump_peer(peer_list[i])
    
    g.write("Peer "+str(i)+": MPU(adversary) : "+str(tot_0)+"/"+str(tot)+" = "+ str(tot_0/tot)+" || Adversary Nodes/Total Nodes : "+str(tot2)+"/"+str(tot)+" = "+ str(tot2/tot)+ " || MPU(total) : "+str(tot)+"/"+str(len(peer_list[i].received_blocks))+" = "+str(tot/len(peer_list[i].received_blocks))+"\n")
    sys.stderr.write("Peer "+str(i)+": MPU(adversary) : "+str(tot_0)+"/"+str(tot)+" = "+ str(tot_0/tot)+" || Adversary Nodes/Total Nodes : "+str(tot2)+"/"+str(tot)+" = "+ str(tot2/tot)+ " || MPU(total) : "+str(tot)+"/"+str(len(peer_list[i].received_blocks))+" = "+str(tot/len(peer_list[i].received_blocks))+"\n")
    
    for block in peer_list[i].received_blocks:
        f.write(str(block.blk_id)+" "+str(block.prev_blk_id)+" "+str(block.time_of_arrival)+" "+str(block.miner_id)+"\n")
        dump(block)
    f.close()

    # For display in the form of a tree
    show(s)
    
g.close()
    