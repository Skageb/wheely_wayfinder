import queue

shared_aruco_queue = queue.Queue()

shared_obstacle_queue = queue.Queue()
#Send int 1 to queue if potential obstacle detected
#Send int 0 to queue if potential obstacle is not an obstacle
#Send int 2 to queue if potential obstacle is confirmed.

