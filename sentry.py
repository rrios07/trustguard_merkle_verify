#this file will hold the functionality to simulate the sentry itself, or the consumer
#in the producer-consumer model

import queue
import cache
import hashlib
import threading
import packet
import csv


#function to process a given data packet. This either consists of caching and verifying its
#contents if it is a merkle packet, storing the value in the root register if it is a root packet,
#or reading the counter line from the cache and concatenating data, counter, and addr
#if it is a data packet
def proc_packet(rec_packet, merkle_cache, root_reg):
    
    #if it is a merkle packet, write the contents to the cache first
    if rec_packet.op == packet.IM_OP:

        #if recv root packet do not perform any writes
        if rec_packet.addr ==  0x10aaae340:
            print("hit root! Not performing a cache write")
            return None, None

        #have to block align child address before writing
        merkle_cache.write_cache_supervised(rec_packet.addr & ~((1 << 6) - 1), rec_packet.way, rec_packet.level, rec_packet.line)
        #if level == 11 (actually level 12) then our parent is root, do not read cache
        if rec_packet.level == 11:
            parent_mac = root_reg.root
        else:
            parent_mac = merkle_cache.read_cache(rec_packet.parentAddr)
        return rec_packet.line, parent_mac

    #if it is a data packet write to output, read associated counter, concatenate, then send to hash engine
    elif rec_packet.op == packet.DATA_OP:
        #first write data to output (do nothing for simulator)
        #next read parent counter from cache
        parent_ctr = merkle_cache.read_cache(rec_packet.parentAddr)
        hmac_in = rec_packet.line + parent_ctr + rec_packet.addr.to_bytes(4, byteorder='big')
        return hmac_in, rec_packet.smac

    else:
        exit("error: unrecognized packet opcode!")



#in a real sentry implementation, the packet reading hardware would send data to the hash engine, 
#multiplex to the appropriate output, and send the address to the level cache for verification, 
#but here we can basically just have the hash engine be in change of this based on the opcode
def hash_engine(input_str, mac, event):

    #print("in hash engine")
    #compute the md5 hash of the input, if mismatch exit with error
    output_hash = hashlib.md5(input_str)
    #print(output_hash.digest())
    #print(mac)
    if output_hash.digest() != mac:
        print("error: mismatching mac!")
        print(output_hash.digest())
        print(mac)

    #once we are done call event.set() to signal the main thread that we are done
    #print("hashes match!")
    event.set()
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
    root_reg = cache.root_reg(b'\x96\x95\xca_S\xcer \x8aj\xef3\xb9.\xef\xd4')

    while True:
        #grab an entry
        if num_engines > 0:
            try:
                val = input_queue.get(timeout=1)
                #print("reading from queue")
                #print("addr: %s, parent_addr: %s" % (hex(val.addr), hex(val.parentAddr)))
                
                #process the next packet in the queue
                input_str, comp_mac = proc_packet(val, merkle_cache, root_reg)
                #spawn thread for the hash engine
                if input_str is not None:
                    num_engines -= 1
                    t = threading.Thread(target = hash_engine, args=(input_str, comp_mac, events[num_engines]))
                    t.start()
            except queue.Empty:
                #if we end up here then the producer stopped producing, we are done
                print(merkle_cache.CACHE_WRITES)
                print(merkle_cache.CACHE_READS)
                cache_stats = [merkle_cache.CACHE_WRITES, merkle_cache.CACHE_READS]
                # Open the file in write mode
                with open("cache_data.csv", 'a', newline='') as file:
                    writer = csv.writer(file)
                    # Write the data to the CSV file
                    writer.writerows(cache_stats)

                print("queue was empty for 3 seconds; we are done receiving")
                exit("queue was empty for 3 seconds!")

        #if we have no engines left we need to wait for at least one one to finish
        else:
            #check for any thread completion; this signifies an engine is done working
            for event in events:
                if event.is_set():
                    event.clear()
                    num_engines += 1