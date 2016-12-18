from CommunicationQueues import comm
from Queue import Empty


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
            try:
                gotten = comm.bc_to_node.get(timeout=2)
            except Empty:
                raise RuntimeError("Expected '" + response + "' got nothing.")
            if gotten[0] == "LOGGING":
                print gotten[1]
                continue
            if gotten[0] == "DEBUG":
                print gotten[1]
                continue
            if gotten[0] == response:
                return gotten
            else:
                raise RuntimeError("Expected '" + response + "' gotten " + str(gotten))

    def expect_wot(self, message):
        response = self.expect("fcpPluginMessage")
        assert response[1] == "plugins.WebOfTrust.WebOfTrust"
        assert response[2]["Message"] == message
        return response[2]

    def respond(self, response):
        global comm
        comm.node_to_bc.put(response)

    def respond_wot(self, response):
        self.respond((response,))
