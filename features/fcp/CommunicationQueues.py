from multiprocessing import Queue


class CommunicationQueues(object):
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
        while not self.bc_to_node.empty():
            print("BC to node:", self.bc_to_node.get())
        while not self.node_to_bc.empty():
            print("Node to BC:", self.node_to_bc.get())


comm = CommunicationQueues()
