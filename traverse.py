#main traversal file. This has the function that will create the controller thread,
#the sentry thread, and the buffer (queue) that is shared by the threads in the 
#producer-consumer model. 

import cache
import tree_levels
import queue
from sentry_controller import verify_range
import threading
from sentry import sentry_sim
import sys

#according to Hansen, there are 12 IM levels including the counter level

num_engines = int(sys.argv[1])
num_ways = int(sys.argv[2])
start = int(sys.argv[3], 16)    #start should be in hex format i.e 0x00... 
length = int(sys.argv[4])       #length should be in decimal
output_queue = queue.Queue(maxsize=100)

#controller_thread = threading.Thread(target = verify_range, args=(0x00000000 + (1 << 12), 1 << 20, 12, 2, "test_file.txt", output_queue))
#controller_thread = threading.Thread(target = verify_range, args=(0x00000000 + (1 << 15), 10000000, 12, num_ways, "test_file.txt", output_queue))
controller_thread = threading.Thread(target = verify_range, args=(start, length, 12, num_ways, "test_file.txt", output_queue))
sentry_thread = threading.Thread(target = sentry_sim, args=(num_engines, 12, num_ways, output_queue))

controller_thread.start()
sentry_thread.start()

controller_thread.join()
sentry_thread.join()
