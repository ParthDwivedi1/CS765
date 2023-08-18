import argparse
from queue import PriorityQueue
import numpy as np
import sys
from copy import deepcopy


class Block:
    def __init__(self,prev_blk_id,blk_id,miner_id,owner,transactions,depth,time,balances):
        self.blk_id=blk_id                          # ID of Block (generated randomly from uuid lib)
        self.prev_blk_id=prev_blk_id                # ID of previous (parent) block
        self.owner=owner                            # ID of Peer in whose blockchain this block is present
        self.miner_id=miner_id                      # ID of Peer which mined the block
        self.transactions=transactions              # List of transactions contained in the block
        self.depth=depth                            # Depth of this block in the blockchain
        self.time_of_arrival=time                   # Time at which this block was received by the Owner
        self.balances=balances.copy()               # The current balances of all Peers after including all transactions from the genesis block till this block (using .copy() to avoid assigning by reference which can lead to errors on modification)

class Transaction:
    def __init__(self,start,destination,coins,size,transaction_id):
        self.transaction_id = transaction_id        # ID of transaction (generated randomly from uuid lib)
        self.start = start                          # ID of peer that sent the coins (if -1 then it is a coinbase transaction)
        self.destination = destination              # ID of peer that received the coins
        self.coins = coins                          # Number of coins involved in the transaction
        self.size = size                            # Size of transaction in Kilobits (by default 8000, since size = 1KB)
        
class Peer:
    def __init__(self,peer_id,speed,power,hashingpower):
        self.id=peer_id                             # ID of Peer          
        self.speed=speed                            # Speed of Peer (whether 'fast' or 'slow')
        self.power=power                            # Power of peer (whether 'lowcpu' or 'highcpu')
        self.received_transactions=[]               # All transactions received by the peer till now
        self.neighbors=[]                           # IDs of all the neighbors of the Peer
        self.left_transactions=[]                   # Transactions that have yet to be included in a block
        self.cacheBlock=[]                          # Due to latency blocks can arrive in different order than expected, this is to store out of order received_block tasks
        self.received_blocks=[]                     # List of all blocks received by the Peer
        self.max_depth=0                            # Maximum depth of the blockchain tree of the Peer till now
        self.hashingpower=hashingpower              # Actual percentage of hashing power possessed by node in the network depending on whether 'highcpu' or 'lowcpu'