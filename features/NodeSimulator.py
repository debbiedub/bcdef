class Block(object):
    pass

class User(object):
    pass

class NodeSimulator(object):
    """Simulating the FCP environment."""
    def __init__(self):
        self.blocks = dict()  # number => Block
        self.users = dict()   # name => User

    def add_block(self, number):
        self.blocks[number] = Block()

    def add_user(self, name):
        self.users[name] = User()
