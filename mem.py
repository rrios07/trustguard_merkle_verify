#this file defines the functions that are responsible for initializing a random memory file
#and writing memory and merkle data to the file

import os
import hashlib
from tree_levels import DELTA, getParentAddr, SMAC_ADDR_START

#opens the provided file for reading and fills the data section with randomized data
#we have 4 GB of data with 64 byte lines so we have 2^26 64 byte lines to write
# 2^26 == 1 << 26
def fill_data(file):

    num_lines = 1 << 26
    #num_lines = 4
    for i in range (num_lines):
        cache_line = os.urandom(64)
        file.write(cache_line)

#function to write counter values to the provided memory file. Counter values will be randomized 
#2-byte value
def fill_counters(file):

    num_counters = 1 << 26 #128MB worth of counters w/ one counter per dataa line is 2^26 counters
    file.seek(0x100000040, 0) #go to counter section of memory
    for i in range(num_counters):
        counter = os.urandom(2)
        file.write(counter) 


#function to calculate a given IM level in the tree. This function will seek to the appropriate place
#in the file to calculate IM values from previous values. NOTE min level here is 2 as that is the 
#level of IM0. NOTE as well that this will NOT work for calculating the root
def fill_im(file, level):
    child_level = level - 1
    base_shift = 21 #IM0 is size 2 << 21, subsequent levels are smaller
    child_addr = DELTA[child_level] 
    parent_addr = DELTA[level]


    shift = base_shift - 2 * (level - 2)

    for i in range(1 << shift): #for each IM node we are calculating
        #get children nodes (64 bytes)
        file.seek(child_addr)
        child_addr = child_addr + 0x40 #move to next child cacheline
        children = file.read(64)
        hash_val = hashlib.md5(children)
        file.seek(parent_addr)
        parent_addr = parent_addr + 0x10 #move to the next IM node location (16 bytes)
        file.write(hash_val.digest())

    return

def calc_root(file):
    prev_addr = DELTA[12]
    root_addr = DELTA[13]

    file.seek(prev_addr)
    final_level = file.read(32) #final IM level is only 32 bytes, but is given an entire cache line
    root = hashlib.md5(final_level)
    file.seek(root_addr)
    file.write(root.digest())
    return

#function to calculate MACs for data section and store them in the memory file
def fill_data_macs(file):

    #for each cache line of data (1 << 26) take the line, find the counter, compute the mac
    num_lines = 1 << 26
    start_addr = DELTA[0]
    counter_addr = DELTA[1]
    end_addr = SMAC_ADDR_START
    for i in range(num_lines):
        file.seek(start_addr)
        line = file.read(64)
        
        file.seek(counter_addr)
        counter = file.read(2) #16-bit counter
        line += counter + start_addr.to_bytes(4, byteorder='big')        #concatenate line, counter, address
        hash_val = hashlib.md5(line)
        file.seek(end_addr)
        file.write(hash_val.digest())
        start_addr += 64
        counter_addr += 2
        end_addr += 16

    return

#function to create the memory file as specified by the TrustGuard memory scheme
def create_memory(file):

    mem_file = open(file, "wb+") #truncate file
    fill_data(mem_file)
    fill_counters(mem_file)

    for i in range(2, 13):      #fill in each IM level
        fill_im(mem_file, i)

    calc_root(mem_file)
    fill_data_macs(mem_file)
    mem_file.close()

#function to read a cacheline of memory at a given address
def read_line(file, addr):

    file.seek(addr)
    line = file.read(64)
    return line

#function to "open" memory in a safe way (read only, binary format)
def open_mem(path):
    return open(path, "rb")





#create_memory("test_file.txt")

#file = open("test_file.txt", "rb")
# fill_data_macs(file)

# mask = ~((1 << 6) - 1)
# start_addr = 0x100000040 + (64 * 1550000)
# for i in range(0, 11):
#     parent_addr = getParentAddr(start_addr)
#     file.seek(start_addr)
#     vals = file.read(64)
#     hash_val = hashlib.md5(vals)
#     file.seek(parent_addr)
#     im_val = file.read(16)
#     print("child address: %s, hash: %s" %(hex(start_addr), hash_val.digest())) 
#     print("parent address: %s, IM: %s" %(hex(parent_addr), im_val))
#     start_addr = parent_addr & mask #get rid off offset bits

# parent_addr = getParentAddr(start_addr)
# file.seek(start_addr) # last im level is a special case; 32 bytes only
# vals = file.read(32)
# hash_val = hashlib.md5(vals)
# file.seek(parent_addr)
# root_val = file.read(16)
# print(root_val)
# print(hash_val.digest()) 

# data_addr = 0x00000000 + (64 * (1 << 26 - 1))
# file.seek(data_addr)
# val = file.read(64)
# file.seek(0x100000040 + (2 * (1 << 26 - 1)))
# ctr = file.read(2)
# val += ctr + data_addr.to_bytes(4, byteorder='big')
# hash_val = hashlib.md5(val)
# file.seek(0x120000000 + (16 * (1 << 26 - 1)))
# hashed_val = file.read(16)
# print(hash_val.digest())
# print(hashed_val)
# #print(hex(getParentAddr(0x100000040 + (64 * 1))))
