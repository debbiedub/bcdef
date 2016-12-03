from CommunicationQueues import comm


class Block(object):
    pass


class User(object):
    def __init__(self, insert):
        self.insert = insert


class NodeSimulator(object):
    """Simulating the FCP environment."""
    def __init__(self):
        global comm
        assert comm.bc_to_node
        assert comm.node_to_bc
        self.blocks = dict()  # number => Block
        self.users = dict()   # name => User

    def add_block(self, number):
        self.blocks[number] = Block()

    def add_user(self, name, insert=False):
        self.users[name] = User(insert)
        
    def expect(self, response):
        global comm
        while comm.bc_to_node:
            gotten = comm.bc_to_node.get(timeout=10)
            if gotten[0] == response:
                return gotten
            else:
                raise RuntimeError("Expected " + response + " gotten " + str(gotten))

    def respond(self, response):
        global comm
        comm.node_to_bc.put(response)
