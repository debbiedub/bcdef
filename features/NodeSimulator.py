from multiprocessing import Pool

class Block(object):
    pass

class User(object):
    def __init__(self, insert):
        self.insert = insert

class NodeSimulator(object):
    """Simulating the FCP environment."""
    def __init__(self):
        self.blocks = dict()  # number => Block
        self.users = dict()   # name => User
        self.processor = Pool(1)

    def add_block(self, number):
        self.blocks[number] = Block()

    def add_user(self, name, insert=False):
        self.users[name] = User(insert)
        
    def call(self, method, **kwargs):
        self.processor.apply_async(method, [], kwargs)

    def shutdown(self):
        self.processor.close()
        self.processor.join()


node_simulator = None
def get(new=False):
    global node_simulator
    if not node_simulator or new:
        node_simulator = NodeSimulator()
    return node_simulator
