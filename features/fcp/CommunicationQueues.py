from multiprocessing import Queue
from logging import Handler

class _CommQueueHandler(Handler):
    def __init__(self, queue):
        Handler.__init__(self)
        self.queue = queue

    def emit(self, record):
        self.queue.put(("LOGGING", record,))


class CommunicationQueues(object):
    """Queues to handle communication between the threads.

    On the bc side, this is also a logging handler sending
    log messages to the node side."""
    def __init__(self):
        self.bc_to_node = Queue()
        self.node_to_bc = Queue()

    def set(self, bc_to_node=None, node_to_bc=None, queues=None):
        if bc_to_node:
            self.bc_to_node = bc_to_node
            return
        if node_to_bc:
            self.node_to_bc = node_to_bc
            return
        assert queues.bc_to_node
        self.bc_to_node = queues.bc_to_node
        assert queues.node_to_bc
        self.node_to_bc = queues.node_to_bc

    def empty_queues(self):
        print "Emptying queues:"
        while not self.bc_to_node.empty():
            print "BC to node:", self.bc_to_node.get()
        while not self.node_to_bc.empty():
            print "Node to BC:", self.node_to_bc.get()
        print "Emptying queues done."

    def get_handler():
        return _CommQueueHandler(self.bc_to_node)


comm = CommunicationQueues()
