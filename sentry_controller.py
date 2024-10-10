#this file will include the functionality related to the sentry control piece of the system
#essentially this will contain the algoirthm that will allow the controller to send 
#instruction packets to the sentry

from tree_levels import DELTA, MAX_LEVEL, getLevel, getParentAddr, SMAC_ADDR_START
import cache
from mem import open_mem, read_line
from packet import send_merkle_packet, send_data_packet, IM_OP, DATA_OP
import queue
from sys import exit


#function to calculate the initial counter ID. This is essentially the absolute position of 
#the counter associated with the input address within the counter line itself. This will be useful
#for determining when to send parent IM nodes with counters. Addr is assumed to be cache line aligned
def calc_counter_id(addr):
    return (addr - DELTA[1]) >> 6 # (addr - DELTA[1]) // 64 I broke this  and didnt realize im so dumb :(((

#function to create a stack of ancestor addresses using a child address 
#and a desired number of levels. Returns the stack length. Assumes an empty stack to start
#levels is the number of ancestors that will be added to the stack NOT including the initial
#child node, which will be added to the stack no matter what
def create_stack(addr, levels, stack):

    #do initialization verification; verify up to root (or root to counter)
    stack.append(addr)
    child_addr = addr & ~((1 << 6) - 1) #no byte offsets; need cache line alignment here
    stack_len = 1
    for i in range(levels):

        parent_addr = getParentAddr(child_addr)
        stack.append(parent_addr)
        stack_len += 1
        child_addr = parent_addr & ~((1 << 6) - 1) #want full child cacheline (not just child node)

    return stack_len

#function to empty the stack. Assumes the stack has at minimum two elements.
#this function pops off stack elements and sends data packets accordingly to 
#the sentry (output queue). Does NOT send the topmost element in the stack as 
#this is the final verification ancestor and not a node to be sent
def empty_stack(stack, stack_len, mem_file, m_cache, output):

    if stack_len < 2:
        exit("Error: stack must have at least two items to start!")
        return -1

    parent_addr = stack.pop()
    stack_len -= 1

    while stack_len > 0:           #while we have things to send
        child_addr = stack.pop()
        child_line = child_addr &  ~((1 << 6) - 1) #grab cacheline address
        if child_line == DELTA[13]: #if we are at root we do not cache the node
            send_merkle_packet(IM_OP, child_line, 13, 0, parent_addr, None, output)
        else:                       #general case; not at root
            #cache the child, recording the level and way for the cache entry
            data = read_line(mem_file, child_line)              #read entire cacheline
            if child_line == DELTA[12]:                         #we only use 32 bytes here
                data = data[0:32]
            level, way = m_cache.write_cache(child_line, data)  #can only write entire cache line (address must be block aligned!)

            send_merkle_packet(IM_OP, child_addr, level, way, parent_addr, data, output)

        parent_addr = child_addr
        stack_len -= 1

#function to determine the number of levels that will need to be added to the stack
#remember that this value does not include the counter line which will always be added to 
#the stack. For instance, if we wanted 3 ancestors added to the stack in addition to the 
#counter line we are adding to the stack, this function would return 3 NOT 4. 
def ancestry(counter_id):
    levels = 1
    while counter_id != 0 and (counter_id & 3 == 0): #counter_id & 3 == counter_id % 4
        levels += 1
        counter_id = counter_id >> 2    #counter_id >> 2 == counter_id // 4
    return levels

#function to send 32 cache lines of data to 'output' starting at the address 'addr'
def send_cache_lines(addr, parent_addr, memory, num_lines, output):

    for i in range(num_lines):
        smac_addr = (addr // 4) + SMAC_ADDR_START
        memory.seek(addr)
        line = memory.read(64)
        memory.seek(smac_addr)
        smac = memory.read(16)
        send_data_packet(DATA_OP, addr, parent_addr, line, smac, i, output)
        addr += 64
        smac_addr += 16
        parent_addr += 2

    return

#function takes a start address, length, and an ouput queue and sends packets
#for verification to the output queue as appropriate to fit the verification 
#algorithm
def verify_range(start, length, levels, ways, mem_file, output):

    #open memory 
    memory = open_mem(mem_file)

    #create a cache instance; this will be used for determining level and way placements
    #so that the merkle packets we send can contain this info 
    merkle_cache = cache.m_cache(levels, ways) #(12, 2) but the ways part is tunable based on number of hash engines
   
    #define a stack of ancestors. This will allow us to pop ancestors off before
    #their children so we can send from root down to counters
    ancestor_stack = []
    
    #first determine the number of cache lines, the initial counter address, 
    end = start + length #get the final address; this will be used for the loop condition
    start = start & ~((1 << 6) - 1) #block align the address first

    level = getLevel(start)
    if level != 0:
        exit("error: must be in data section for verification")

    #get first counter and the corresponding counter ID
    counter_addr = getParentAddr(start)

    #do initialization verification; verify up to root (or root to counter)
    #this first path is unique in that it must go all the way to root no matter what. 
    #Future counter values will only have to go up based on their ID, but for this counter it is not the case

    stack_len = create_stack(counter_addr, MAX_LEVEL - 2, ancestor_stack)
    empty_stack(ancestor_stack, stack_len, memory, merkle_cache, output)
    
    #Send first data counter here
    #TODO: get this to work so we can start sending in the middle of a counter line
    #print(counter_addr & ((1 << 6) - 1))
    num_lines = 32 - ((counter_addr & ((1 << 6) - 1)) >> 1) & 31 # 32 - ((offset / 2) % 32)
    #print(num_lines)
    send_cache_lines(start, counter_addr, memory, num_lines, output)

    #increment address of current data and counter and calculate counter id
    start += (num_lines << 6) #num_lines * 64
    counter_addr += (num_lines << 1 )  #num_lines * 2
    counter_id = calc_counter_id(counter_addr & ~((1 << 6) - 1)) #must align counter to cache line boundary 
    #send counters and data 
    while start < end:
        #print("processing counter with id == %d" % counter_id)
        num_ancestors = ancestry(counter_id)
        #print("c_id: %d, num_ancestors: %d" % (counter_id, num_ancestors))
        stack_len = create_stack(counter_addr, num_ancestors, ancestor_stack)
        empty_stack(ancestor_stack, stack_len, memory, merkle_cache, output)

        #special case where we may have less than 32 lines to send. Will also handle if we have exactly 32 lines left to send
        if end - start < 2048:
            num_lines = ((end - start - 1) >> 6) + 1    # ((end - start - 1) // 64) + 1 == number of lines to send
            print("processing %d extra lines" % num_lines)
            send_cache_lines(start, counter_addr, memory, num_lines, output)
        else:
            #Send corresponding data here
            send_cache_lines(start, counter_addr, memory, 32, output)

        counter_addr += 64 #go to next counter group
        start += 2048    #go to next set of data cache lines
        counter_id += 1


    #merkle_cache.print_cache()
    #print(counter_id)
    return

#output_queue = queue.Queue(maxsize=100)

#verify_range(0x00000000 + (1 << 12), 1 << 20, 12, 2, "test_file.txt", output_queue)
#verify_range(0x00000000 + 2 * (1 << 11), 34816, 12, 2, "test_file.txt", None)
