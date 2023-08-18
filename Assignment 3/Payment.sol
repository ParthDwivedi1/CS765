// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract Payment {
  
  uint[] public user_list; // Maintains a list of user ids
  mapping(uint => string) public id2names; // A mapping of user ids to names of users
  mapping(uint => uint) public id2index; // A mapping of user ids to indices (for maintenance of graph edges)


  event CreateAccount(uint user_id1, uint user_id2, uint balance, bool status); // Event that tells about the success or failure of account creation
  event UserRegister(uint user_id, string user_name, bool status); // Event that tells about the success or failure of user registration
  event CloseAccount(uint user_id1, uint user_id2, bool status); // Event that tells about the success or failure of account closure
  event AmountSend(uint user_id1, uint user_id2, uint balance, bool status); // Event that tells about the success or failure of sending an amount

  // Struct to maintain edges between nodes
  struct Edge{

    uint index1; // Stores the starting node of the edge
    uint index2; // Stores the ending node of the edge
    uint bal_user_1; // The balance belonging to the start node
    uint bal_user_2; // The balance belonging to the end node
  }

  Edge[150][150] public edges; // Structure to store the edges
  uint[150] public degrees; // Structure to store the degrees of nodes

  constructor() {
  }
  function registerUser(uint user_id, string memory user_name) public returns (bool) {
    
    bool exists=false;

    // Checking if the user already exists
    for(uint i=0;i<user_list.length;i++){

      if(user_list[i]==user_id){

        exists=true;
        break;
      }
    }

    // If user already exists, return false
    
    if(exists){
      emit UserRegister(user_id, user_name, false);
      return false;
    }else{
      
      // Add user to mapping to ids and names
      id2names[user_id]=user_name;
      // Add user to list of users
      user_list.push(user_id);
      // Add user to mapping of ids and indices
      id2index[user_id]=user_list.length;
      emit UserRegister(user_id, user_name, true);
      return true;
    }
  }

  // Function to create an amount between any two users with given balance

  function createAcc(uint user_id1, uint user_id2, uint balance) public returns (bool) {

    // If any of the user ids is not registered, return false
    if(id2index[user_id1]==0 || id2index[user_id2]==0){
      emit CreateAccount(user_id1, user_id2, balance, false);
      return false;
    }

    // Add edges in both directions, from 1 to 2, and 2 to 1

    Edge memory edge1=Edge({index1:id2index[user_id1],index2:id2index[user_id2],bal_user_1:balance/2,bal_user_2:balance-balance/2});
    Edge memory edge2=Edge({index1:id2index[user_id2],index2:id2index[user_id1],bal_user_1:balance-balance/2,bal_user_2:balance/2});

    // Add the edge to edge list of appropriate nodes and increment degrees
    edges[edge1.index1][degrees[edge1.index1]]=(edge1);
    degrees[edge1.index1]+=1;

    // Add the edge to edge list of appropriate nodes and increment degrees
    edges[edge2.index1][degrees[edge2.index1]]=(edge2);
    degrees[edge2.index1]+=1;
    emit CreateAccount(user_id1, user_id2, balance, true);

    return true;
  }

  // Function to send an amount from one user to another

  function sendAmount(uint user_id1,uint user_id2,uint balance) public returns (bool) {

    uint st=id2index[user_id1];
    uint end=id2index[user_id2];

    // If any of the user_ids is not registered, return false
    if(st==0 || end==0){
      emit AmountSend(user_id1, user_id2, balance, false);
      return false;
    }

    bool exists=false;

    // If a direct edge does not exist, return false

    for(uint i=0;i<degrees[st];i++){

      if(edges[st][i].index2==end){
        edges[st][i].bal_user_1-=balance;
        edges[st][i].bal_user_2+=balance;
        exists=true;
        break;
      }
    }

    if(!exists){
      emit AmountSend(user_id1, user_id2, balance, false);
      return false;
    }

    for(uint i=0;i<degrees[end];i++){

      if(edges[end][i].index2==st){
        edges[end][i].bal_user_1+=balance;
        edges[end][i].bal_user_2-=balance;
        break;
      }
    }

    // Since this is only being called by the client.py file
    // calls are made such that the balance at the sending node will
    // always be > 0

    emit AmountSend(user_id1, user_id2, balance, true);
    return true;
  }

  // Function to close the account between any two users

  function closeAccount(uint user_id1,uint user_id2) public returns (bool){

    uint st=id2index[user_id1];
    uint end=id2index[user_id2];
    uint ind=100000000;

    // Search for the edge to be removed

    for(uint i=0;i<degrees[st];i++){

      if(edges[st][i].index2==end){

        ind=i;
        break;
      }
    }

    // If edge does not exist, return false

    if(ind==100000000){
      emit CloseAccount(user_id1, user_id2, false);
      return false;
    }

    // To remove, copy the last edge to the index of
    // edge to be deleted and decrement degree

    edges[st][ind]=edges[st][degrees[st]-1];

    degrees[st]-=1;

    // Perform the same process for the complementary edge
    // in the reeverse direction

    ind=100000000;

    for(uint i=0;i<edges[end].length;i++){

      if(edges[end][i].index2==st){

        ind=i;
        break;
      }
    }

    if(ind==100000000){
      emit CloseAccount(user_id1, user_id2, false);
      return false;
    }

    // Same as above, copying the last edge to the index
    // of edge to be deleted and decrementing degree

    edges[end][ind]=edges[end][degrees[end]-1];

    degrees[end]-=1;

    emit CloseAccount(user_id1, user_id2, true);
    return true;
  }

  // Function to return the balance of any user
  function getBalance(uint user_id1) public view returns (uint){

    // Sum up the balances on all edges having start as
    // the given user id

    uint st=id2index[user_id1];
    uint tot=0;
    for(uint i=0;i<edges[st].length;i++){
      tot+=edges[st][i].bal_user_1;
    }

    return tot;
  }
 
}
