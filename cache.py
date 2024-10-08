import tree_levels

class root_reg:

    def __init__(self, root=None):
        self.root = root #this is the 16 byte root MAC itself

class m_cache_line:

    def __init__(self):
        self.valid = 0
        self.tag = 0 #this will be entire address excluding the byte offset bits
        self.data = bytearray(64) #64 byte cachline

    def __str__(self):
        return f'valid: {self.valid}, tag: {hex(self.tag)}, data: {self.data}'

class m_cache_set:  

    def __init__(self, ways):
        self.lines = [m_cache_line() for i in range(ways)]

class m_cache:  #will have one set per level in the tree (not including data or root)

    def __init__(self, levels, ways):
        self.sets = [m_cache_set(ways) for i in range(levels) ]
        self.levels = levels
        self.ways = ways

    #print the contents of our cache
    def print_cache(self):

        levels = self.levels
        ways = self.ways

        for level in range(levels): #for each level
            for way in range(ways):
                if level != 11:
                    print("level %d, way %d: %s" % (level, way, self.sets[level].lines[way]))

    #function to write to the cache with way and level pre-specified. This will emulate the 
    #sentry side functionality where cache controlling is done by the controlling side. If we 
    #continue working on this system eventually the control will exist in hardware, and so there
    #will simply be a single cache controller instead of this supervised cache mirroring method
    def write_cache_supervised(self, addr, way, level, data):

        self.sets[level].lines[way].valid = 1
        self.sets[level].lines[way].tag = addr
        self.sets[level].lines[way].data = data[:]
        return


    #given an address write to our cache. Addr is a 32 bit address (assumed to be block aligned) and
    #data is a 64 length byte array. If all ways are full removes the data with the lower address
    #as this data will no longer need to be used. Returns the level and way that the cache line
    #was written to
    def write_cache(self,addr, data):

        #write location is based on level
        level = tree_levels.getLevel(addr) - 1 #lowest cached level is level 1 which is index 0, so need to decrement 1
        cache_set = self.sets[level]   
        #print(cache_set)   
        #tag = addr & ~((1 << 6) - 1) #don't need this because we are already block aligned w cacheline
        tag = addr
        min_addr = cache_set.lines[0].tag         #if none are invalid we replace based on min address
        min_way = 0
        #first check to see if any entries are invalid
        for way in range(len(cache_set.lines)):
            if cache_set.lines[way].tag < min_addr:
                min_addr = cache_set.lines[way].tag
                min_way = way
            if cache_set.lines[way].valid == 0:
                self.sets[level].lines[way].valid = 1
                self.sets[level].lines[way].tag = tag
                self.sets[level].lines[way].data = data[:]
                return (level, way)
        
        #print("set is full; replacing smallest address")
        self.sets[level].lines[min_way].tag = tag
        self.sets[level].lines[min_way].data = data[:]
        return (level, min_way)
    
    #function to read a value from the cache. If the parent address
    #is a counter line the read will return a 2-byte counter value
    #otherwise a 16-byte IM hash is returned. Designed this way since the getParentAddr()
    #function will return the byte offset included address that will correspond to the parent node
    def read_cache(self, addr):
        level = tree_levels.getLevel(addr) - 1 #lowest cached level is level 1 which is index 0, so need to decrement 1 
        cache_set = self.sets[level]   
        #print(cache_set)
        tag = addr & ~((1 << 6) - 1) 
        offset = addr & ((1 << 6) - 1)

        #first check to see if any entries are invalid
        for way in range(len(cache_set.lines)):

            if cache_set.lines[way].tag == tag:
                if level == 0: #parent is a counter
                    return cache_set.lines[way].data[offset : offset + 2]
                else:
                    return cache_set.lines[way].data[offset : offset + 16]
        
        #if we get here it was a cache miss
        print("cache miss occurred")
        #self.print_cache()
        return -1

#initialize a cache object. There should be a set for each level in the tree
#the minimum number of ways is dependent upon how many hash engines we have to 
#use at our disposal; likely 2 ways will be sufficient. Root and data
#levels will NOT exist in this cache. The number of levels in the cache should
#be equal to the number of IM levels + an extra level for counters
def init_cache(levels, ways):
    return m_cache(levels, ways)






