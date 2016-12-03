class Dummy(object):
    pass

class XMLFile(object):
    def __init__(self, path):
        self.bcdef_participant = Dummy()
        self.bcdef_participant.block_data = Dummy()
        self.bcdef_participant.block_data.identity = Dummy()
        self.bcdef_participant.block_data.identity._text = "block"    
