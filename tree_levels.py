from sys import exit

DELTA = [ 
  0x00000000, #start addr for data       => 4G; level 0
  0x100000040, #start addr for counter   => 128M; level 1
  0x108000080, #start addr for IM0       => 32M; level 2
  0x10a0000c0, #IM1  => 8M
  0x10a800100, #IM2  => 2M
  0x10aa00140, #IM3  => 512K
  0x10aa80180, #IM4  => 128K
  0x10aaa01c0, #IM5  => 32K
  0x10aaa8200, #IM6  => 8K
  0x10aaaa240, #IM7  => 2K
  0x10aaab280, #IM8  => 512B
  0x10aaac2c0, #IM9  => 128B
  0x10aaad300, #IM10 => 32B
  0x10aaae340, #root start => 16B          level 13
  0x10aaaf380 #root end => 16B; need this for level calculation logic to work
]

SMAC_ADDR_START = 0x120000000
SMAC_ADDR_END = 0x160000000

MAX_LEVEL = 15 #maximum level in the tree; think this might actually be 13

#function to calculate the level in the tree of an address
def getLevel(addr):
    for level in range(MAX_LEVEL - 1):
        if (addr >= DELTA[level]) and (addr < DELTA[level + 1]):
            return level;
    exit("get level failed") #could not find level in tree for this address; abort

#function to calculate a parent address using a given child address.
#NOTE: the child address must be a multiple of 64 aka cache line aligned
#so mask as necessary with a given address before passing it to this function
def getParentAddr(childAddr):

    for level in range(MAX_LEVEL - 1):
        if (childAddr >= DELTA[level]) and (childAddr < DELTA[level + 1]):
            delta = childAddr - DELTA[level]
            if level == 0:
                delta = delta // 32
            else:
                delta = delta // 4
            parentAddr = DELTA[level + 1] + delta
            return parentAddr

    exit("get parent address failed\n")
