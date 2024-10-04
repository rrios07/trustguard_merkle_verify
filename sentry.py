#this file will hold the functionality to simulate the sentry itself, or the consumer
#in the producer-consumer model

import queue
import cache
import hashlib
import threading

#function to process a given data packet. This either consists of caching and verifying its
#contents if it is a merkle packet, storing the value in the root register if it is a root packet,
#or MACing the data if its a data packet
def proc_packet():
    
    #if it is a merkle packet, write the contents to the cache first

    #if it is a data packet, read associated counter, concatenate, then send to hash engine
    return


#in a real sentry implementation, the packet reading hardware would send data to the hash engine, 
#multiplex to the appropriate output, and send the address to the level cache for verification, 
#but here we can basically just have the hash engine be in change of this based on the opcode
def hash_engine(input_str, op_code, parent_addr, merkle_cache, event):

    #compute the md5 hash of the input

    #if we are hashing a merkle 

    #once we are done call event.set() to signal the main thread that we are done


    return


def sentry_sim(num_engines, levels, ways, input_queue):
    
    #NOTE: not sure if need this, but maybe have an array of locks, one for each level in the cache?
    #then lock then writing to or reading from the cache at that level

    #define thread events for communication from hash threads; one event per hash engine
    #to allow for one signal from each thread back to the main sentry
    events = []
    for i in range(num_engines):
        events.append(threading.Event())

    #define the cache
    merkle_cache = cache.m_cache(levels, ways)

    #define root register
    root_reg = cache.root_reg()

    while True:
        #grab an entry
        if num_engines > 0:
            num_engines -= 1
            try:
                val = input_queue.get(timeout=3)
                print("addr: %s, parent_addr: %s" % (hex(val.addr), hex(val.parentAddr)))
                
                #process the next packet in the queue
                proc_packet()
                #spawn thread for the hash engine
                threading.Thread(target = hash_engine, args=(input_str, op_code, parent_addr, merkle_cache, event))
            except queue.Empty:
                #if we end up here then the producer stopped producing, we are done
                exit("queue was empty for 3 seconds!")

        #if we have no engines left we need to wait for at least one one to finish
        else:
            #check for any thread completion; this signifies an engine is done working
            for event in events:
                if event.is_set():
                    event.clear()
                    num_engines += 1

            
