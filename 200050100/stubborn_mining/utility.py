import numpy as np
import uuid
from structures import Block, Peer, Transaction
from copy import deepcopy


MININGFEE = 50

# Generation of a new transaction
def transaction_generation(peer,block,meantransactiontime,current_time):
    
    inter_arrival_time = np.random.exponential(scale=meantransactiontime) # Generating the inter-arrival time between 2 transactions
    
    # Randomly fixing the destination ID of Peer, ensuring that sender is not the same as destination
    dest=peer.id 
    
    while dest==peer.id:
        dest=np.random.randint(len(block.balances))
        
    # Creating a transaction object with the parameters described above
    # Number of coins is taken as a random small amount
    # This pretty much ensures that balance never goes below 0 and that all transaction generated are valid
    
    transaction=Transaction(peer.id,dest,np.random.random()*2,8000,uuid.uuid4())
    
    dump_transaction(transaction)
    
    # Task is generated in the correct format specified in simulator.py 
    return ([current_time+inter_arrival_time,peer.id,'gen_transaction',transaction])
    pass

# Find the block with max depth and minimum timestamp of a Peer, that is to be mined upon
def find_mining_block(peer):
    block=None
    max_depth=0
    time_of_arrival=np.inf
    
    # Iterate over all blocks and find the block with max depth. If there is a tie for maximum depth, choose the block with least time of arrival
    for blk in peer.received_blocks:
        if blk.depth>max_depth:
            max_depth=blk.depth
            time_of_arrival=blk.time_of_arrival
            block=blk
        elif blk.depth==max_depth and blk.time_of_arrival<time_of_arrival:
            time_of_arrival=blk.time_of_arrival
            block=blk            
    
    return block

# Generation of a new block 

def block_generation(peer,meanblocktime,current_time):
    
    # Generating the inter arrival time between 2 blocks
    
    inter_arrival_time = np.random.exponential(scale=meanblocktime/peer.hashingpower)
    
    # Finding the block in the chain that is to be mined upon
    
    if(peer.id==0 and peer.attacker_lead!=0):
        prev_block = peer.secret_chain[-1][4]
        prev_blk_id = prev_block.blk_id
    else:
        prev_block = find_mining_block(peer)
        prev_blk_id = prev_block.blk_id
    
    # Choosing a random number of transactions from the generated transactions with a cap of 999 (1 left for coinbase transaction)
    # Since the transactions are generated while keeping the balances >=0 for all nodes, all transactions are valid
    
    # There are some theoretical edge cases where balance may become negative involving latency and different order of transactions
    # But such cases never occurred in any of our simulations with widely different parameters, hence taking it as an extremely low probability event.
    
    number_of_transactions=min((int)(np.random.random()*len(peer.left_transactions)),999)
    included_transactions = peer.left_transactions[:number_of_transactions]
    
    # Including coinbase transaction
    
    included_transactions.append(Transaction(-1,peer.id,MININGFEE,8000,uuid.uuid4()))
    
    # Updating the left_transactions (Transactions to be included in a block)
    peer.left_transactions=peer.left_transactions[number_of_transactions:]
    
    # Creating a block object with the parameters described above
    
    block=Block(prev_blk_id,uuid.uuid4(),peer.id,peer.id,included_transactions,prev_block.depth+1,current_time+inter_arrival_time,[])
    
    # Task is generated in the correct format specified in simulator.py 
    
    return ([current_time+inter_arrival_time,peer.id,'gen_block',block])
    pass

# Returns delay latency between two nodes with IDs given by start and dest, for a packet of given size, and given rho as speed of light propagation delay

def latency(start,dest,size,rho):
    
    #Link speed between the two nodes in KiloBits per second
    c=5000 
    
    if(start.speed=='fast' and dest.speed=='fast'):
        c=100000 # Setting to 100 Mbps if both nodes are fast
    
    
    d = np.random.exponential(scale=96/c) # Queuing Delay Calculation
     
    delay = rho+((size)/c)*1000+d # Total delay latency
    return delay

# Returns depth of block with given block ID, if not found, returns -1

def find_block_depth(blk_id,peer):

    # First it checks the already received blocks
    for block in peer.received_blocks:
        if block.blk_id == blk_id:
            return block.depth
    
    # If not found in received blocks, then check the secret chain
    for task in peer.secret_chain:
        if task[4].blk_id == blk_id:
            return task[4].depth
    
    return -1

# Broadcasts a given task from Peer object start to a Peer object dest

def broadcast(task,start,dest,rho):
    
    # Calculation of size of packet to be transmitted
    size=0
    if(task[2] == 'received_transaction'):
        size = task[4].size
    elif (task[2] == 'received_block'):
        size = len(task[4].transactions)*8000 # Since each transaction is of 1KB
    else:
        # This will never happen because type of task can only be receiving of a block or a transaction
        print("Illegal Task Type")
        exit(50)
        
    # Calculating the delay latency to find at what time the event is to be scheduled
    delay = latency(start,dest,size,rho)
    
    # Creating a new task at time = current time + delay
    # ID of node receiving the message is dest.id
    # task[2] refers to type of task (received_block or received_transaction)
    # ID of node from which message is received is start.id
    # Details of Transaction/Block is in task[4] (can use reference here, because on processing we always create a new copy of Block and Transaction is same for different peers)
    
    newtask = [task[0]+delay, dest.id , task[2] , start.id , task[4]]
    
    return newtask

# Checks if a transaction with a given ID exists in a given Peer object. If true, returns 1, else returns -1.

def exists_transaction(transaction_id,peer):

    #Checking if a transaction exists or not
    for transaction in peer.received_transactions:
        if(transaction.transaction_id == transaction_id):
            return 1
    return -1

# Gets balance of all peers according to the Blockchain of a given Peer object till the block with given Block ID
def get_balance(peer,blk_id):
    
    # First it checks the already received blocks
    for block in peer.received_blocks:
        if block.blk_id==blk_id:
            return block.balances.copy()
        
    # If not found, then it checks the secret_chain
    for task in peer.secret_chain:
        if task[4].blk_id==blk_id:
            return task[4].balances.copy()
        
    return []
    
# Validates all transactions given in a block and updates the balances in the block and the list of left_transactions in the Peer object

def validate(block,peer):
    
    # Get balances of all peers till the previous block ID
    balances = get_balance(peer,block.prev_blk_id).copy()
    
    # For each transaction, we update the balances of the peers
    dump(block)
    print(balances)
    for transaction in block.transactions:
        
        if(transaction.start!=-1):
            # Deduct from Sender node only if not coinbase transaction
            
            balances[transaction.start]-=transaction.coins
        # dump(block)    
        balances[transaction.destination]+=transaction.coins
    
    # If ever balance is 0, validation has failed
    for bal in balances:
        if bal<0:
            return False
        
    # Updating balances in the current block
    block.balances=balances.copy()

    # Only transactions that are a left to be included and not included in the current block are in left_transactions
    not_present=[]
    
    for transaction in peer.left_transactions:
        if transaction not in block.transactions:
            not_present.append(transaction)
    
    peer.left_transactions=not_present
    
    return True

# Finds the maximum depth of a block that was mined by the same node itself
# Used when the attacker tries to find if a block is to be dropper
def find_own_max_depth(peer):
    max_depth=0
    
    # First iterate over all received_blocks
    for block in peer.received_blocks:
        if(block.miner_id==peer.id):
            max_depth=max(max_depth,block.depth)
    
    # Then iterate over blocks in secret_chain
    for task in peer.secret_chain:
        if(task[4].miner_id==peer.id):
            max_depth=max(max_depth,task[4].depth)
    
    return max_depth

# Similar to validate but we don't update any parameters about the block
def validate_not_update(block,peer):
    
    # Get balances of all peers till the previous block ID
    balances = get_balance(peer,block.prev_blk_id).copy()
    
    # For each transaction, we update the balances of the peers
    for transaction in block.transactions:
        
        if(transaction.start!=-1):
            # Deduct from Sender node only if not coinbase transaction
            balances[transaction.start]-=transaction.coins
        # dump_transaction(transaction)
        # print(balances)
        # dump(block)
        balances[transaction.destination]+=transaction.coins
    
    # If ever balance is 0, validation has failed
    for bal in balances:
        if bal<0:
            return False
    
    return True
    
# Adding the blocks that have been cached back into the blockchain

# block is the most recent addition to the blockchain, task_list is the list of tasks, and peer_list is an array of all the Peer objects
def add_cache(task_list,peer_list,peer,block,rho,current_time):
    
    check=0
    rem_task=None
    # Iterating over all tasks that have been cached
    
    for nexttask in peer.cacheBlock:
        rem_task=nexttask
        if nexttask[4].prev_blk_id != block.blk_id:
            # On not finding a block that comes next in chain, skip
            continue
        
        # When we find a block that comes next in chain
        
        # Update the depth of the cached block
        nexttask[4].depth=block.depth+1
        
        # Validating the arrived block
        
        if(validate(nexttask[4],peer)):
            
            #First, max_depth and received_blocks are updated
            
            peer.max_depth=max(peer.max_depth,nexttask[4].depth) # Updating the maximum depth of the Peer Object
            peer.received_blocks.append(nexttask[4]) # Appending the new block to the list of blocks
            
            # Broadcast to neighbors, except where it is received from
            # Broadcast only if not the attacker node
            # This is to be done only if the node is honest
            
            # The process if it is an attacker node follows similar to what is there in simulator.py
            if(peer.id!=0):
                for adjacent in peer.neighbors:
                    if adjacent == nexttask[3]:
                        continue
                    ntask = broadcast(nexttask,peer,peer_list[adjacent],rho)
                    task_list.put(ntask)
                    print("Added only:- ",ntask)
            elif (nexttask[4].miner_id!=0):
                
                # If attacker lead is greater than or equal to 2,
                # the attacker node, broadcasts exactly one node,
                # keeping the rest of the chain secret.
                
                # Obviously it does not broadcast the honest node received
                
                # Broadcasting the secret node to neighbors
                
                if peer.attacker_lead>=2:
                    for adjacent in peer_list[nexttask[1]].neighbors:
                        if adjacent == nexttask[3]:
                            continue
                        peer_list[nexttask[1]].secret_chain[0][0]=current_time
                        ntask = broadcast(peer.secret_chain[0],peer,peer_list[adjacent],rho)
                        task_list.put(ntask)
                        print("Added only:- ",ntask)
                        
                    # The attacker lead is updated
                    peer.attacker_lead-=1

                    # Added the secret block to list of received blocks
                    peer.received_blocks.append(peer.secret_chain[0][4])    
                    
                    # Updated the max_depth
                    peer.max_depth=max(peer.max_depth,peer.secret_chain[0][4].depth)                         
                    
                    # Removed the block from the secret chain
                    peer.secret_chain=peer.secret_chain[1:]

                
                elif peer.attacker_lead==1:
                    for adjacent in peer.neighbors:
                        if adjacent == nexttask[3]:
                            continue
                        peer.secret_chain[1][0]=nexttask[0]
                        ntask = broadcast(peer.secret_chain[1],peer,peer_list[adjacent],rho)
                        task_list.put(ntask)
                        print("Added only:- ",ntask)

                    # Updating attacker lead
                    peer.attacker_lead=0
                    # Added secret block to list of received blocks
                    peer.received_blocks.append(peer.secret_chain[0][4])
                    
                    # Updated the max_depth
                    peer.max_depth=max(peer.max_depth,peer.secret_chain[0][4].depth)
                    
                    # Empty the secret_chain of the attacker node
                    peer.secret_chain=[]
            else:
                # Finally if the attacker node receives a block mined by itself
                # Then add this block (actually task) to the secret chain
                
                # Updating the value of task[4] so that the value of block depth
                # and other updated parameters are saved in the block
      
                ntask=deepcopy(nexttask)
                peer.secret_chain.append(ntask)
                peer.attacker_lead+=1
                pass

            # Checking if there are any other blocks to add from cache
            check=1
            break
            add_cache(task_list,peer_list,peer,block,rho)
            return add_cache(task_list,peer_list,peer,nexttask[4],rho)
        else:
            # Setting previous block id to a non existent block, ensuring that this block will never be considered again
            nexttask[4].prev_blk_id=-2
            check=2
            break
            
            # Checking if there are any other blocks that build upon the current block
            return add_cache(task_list,peer_list,peer,block,rho)
    
    
    # check=0 represents that there are no more cache blocks to be added
    # Function is terminated here
    
    # check=1 represents that there might be a chain on both the blocks added
    # Hence a recursive call is done on both blocks
    
    # check=2 represents that the block was invalidated and hence this cannot be
    # a part of the chain and hence the recursive call is done on only the original block
    
    if(check==0):
        return False
    elif(check==1):
        peer.cacheBlock.remove(rem_task)
        add_cache(task_list,peer_list,peer,block,rho,current_time)
        return add_cache(task_list,peer_list,peer,nexttask[4],rho,current_time)
    else:
        peer.cacheBlock.remove(rem_task)
        return add_cache(task_list,peer_list,peer,block,rho,current_time)
        
    return False

# Check if a transaction exists in a received block

def exists_transaction_in_blocks(transaction,peer):
    
    for blk in peer.received_blocks:
        if transaction in blk.transactions:
            return True
    return False

# Check if a block exists in cache

def exists_in_cache(blk_id,peer):
    for task in peer.cacheBlock:
        if task[4].blk_id == blk_id:
            return True
        
    return False

# Printing function for debugging purposes
def dump_transaction(ele):
    print("Transaction ID: ",ele.transaction_id)
    print("Transaction Start: ",ele.start)
    print("Transaction Destination: ",ele.destination)
    print("Transaction Coins: ",ele.coins)
    print("Transaction Size: ",ele.size)
        


# Printing function for debugging purposes
def dump_transactions(transactions):
    for ele in transactions:
        dump_transaction(ele)        
# Printing function for debugging purposes

def dump(block):
    print("Block ID: ",block.blk_id)
    print("Prev Block ID: ",block.prev_blk_id)
    print("Block Miner ID: ",block.miner_id)
    print("Block Owner ID: ",block.owner)
    print("Transactions: ",len(block.transactions))
    dump_transactions(block.transactions)
    print("Depth: ",block.depth)
    print("Arrival Time: " ,block.time_of_arrival)
    print("Balances: ",block.balances)
    
    
def dump_peer(peer):
    print("Peer ID: ",peer.id)
    print("Speed: ",peer.speed)
    print("Power: ",peer.power)
    print("Hashing Power: ",peer.hashingpower)
    print("Max Depth: ",peer.max_depth)
    print("Balances: ",peer.attacker_lead)
    