#main traversal file. This has the function that will create the controller thread,
#the sentry thread, and the buffer (queue) that is shared by the threads in the 
#producer-consumer model. 

import cache
import tree_levels
import queue
from sentry_controller import verify_range
import threading
from sentry import sentry_sim

#according to Hansen, there are 12 IM levels including the counter level
# my_cache = cache.init_cache(12, 2) 
# #print(my_cache.sets)

# byte_vals = bytearray(64)
# byte_vals[0] = 0xaa

# # print(tree_levels.getLevel(0x10aaaa250))
# # print(hex(tree_levels.getParentAddr(0x10aaae340)))
# my_cache.write_cache(0x10aaaa280, byte_vals)
# #my_cache.print_cache()
# byte_vals[0] = 0xbb
# my_cache.write_cache(0x10aaaa3c0, byte_vals)
# byte_vals[0] = 0xcc
# byte_vals[-1] = 0xdd 
# my_cache.write_cache(0x10aaaa400, byte_vals)


# my_cache.print_cache()

# print(my_cache.read_cache(0x10aaaa400 + 16))

# print(hex(tree_levels.getParentAddr(0x000))) 
# print(hex(0x10aaae340 &  ~((1 << 6) - 1)))

output_queue = queue.Queue(maxsize=100)

controller_thread = threading.Thread(target = verify_range, args=(0x00000000 + (1 << 12), 1 << 20, 12, 2, "test_file.txt", output_queue))
sentry_thread = threading.Thread(target = sentry_sim, args=(output_queue, ))

controller_thread.start()
sentry_thread.start()

controller_thread.join()
sentry_thread.join()
#verify_range(0x00000000 + (1 << 12), 1 << 20, 12, 2, "test_file.txt", output_queue)