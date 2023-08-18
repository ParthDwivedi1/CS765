from treelib import Tree, Node
import sys
import subprocess

def show(file_name):
    
    f = open(file_name,'r')
    
    lines = f.readlines()
    f.close()
    tree=Tree()
    
    for line in lines:
        line=line.strip().split()
        # print("Hello")
        if line[1] == '-1':
            tree.create_node(line[2],line[0])
        else:
            tree.create_node(str(line[2])+"\n"+str(line[0])+"\n"+str(line[3]),line[0],line[1])
    
    tree.to_graphviz(file_name[:-3]+"dot")
    output=subprocess.check_output(['dot','-Tpdf',file_name[:-3]+"dot"])
    
    f = open(file_name[:-3]+"pdf",'wb')
    f.write(output)
    f.close()
    # subprocess.check_call(['rm','temp.dot'])
    # subprocess.check_call(['rm',file_name])
    