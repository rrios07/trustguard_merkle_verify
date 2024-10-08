#file to define all sentry packet structure information
#can send the sentry a packet to verify a merkle node or to 
#verify a data line

import queue

IM_OP = 7
DATA_OP = 8

class merkle_packet:
    
    def __init__(self, op, addr, level, way, parentAddr, line):
        self. op = op
        self.addr = addr
        self.level = level
        self.way = way
        self.parentAddr = parentAddr
        self.line = line

class data_packet:

     def __init__(self, op, addr, parentAddr, line, smac):
        self. op = op
        self.addr = addr
        self.parentAddr = parentAddr
        self.line = line   
        self.smac = smac


#function to send a merkle packet to the sentry
def send_merkle_packet(op, addr, level, way, parentAddr, line, output):
    #print("addr: %s, parent_addr: %s" % (hex(addr), hex(parentAddr)))

    packet = merkle_packet(op, addr, level, way, parentAddr, line)
    output.put(packet)
    return

#function to send a data packet to the sentry
def send_data_packet(op, addr, parentAddr, line, smac, output):
    #print("addr: %s, parent_addr: %s" % (hex(addr), hex(parentAddr)))

    packet = data_packet(op, addr, parentAddr, line, smac)
    output.put(packet)
    return