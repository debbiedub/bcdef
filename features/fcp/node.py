from CommunicationQueues import comm


DETAIL = object()


        
class FCPNode(object):
    def __init__(self, verbosity):
        assert verbosity == DETAIL
        global comm
        assert comm
        assert comm.bc_to_node
        comm.bc_to_node.put(("DEBUG", "Node __init__...",))
        comm.bc_to_node.put(("hello",))
        self.wait_for("olleh")
        comm.bc_to_node.put(("DEBUG", "Node __init__...done",))
        
    def wait_for(self, response=None):
        if response:
            expected = "'" + str(response) + "'"
        else:
            expected = "anything"

        global comm
        assert comm
        assert comm.node_to_bc
        comm.bc_to_node.put(("DEBUG", "Node wait_for " + expected + "...",))
        while True:
            try:
                gotten = comm.node_to_bc.get(timeout=2)
            except Empty:
                comm.bc_to_node.put(("DEBUG", "Node wait_for " + expected + " got nothing.",))
                raise RuntimeError("Expected " + expected + " got nothing.")
            comm.bc_to_node.put(("DEBUG", "Node wait_for " + expected + " got '" + str(gotten) + "'.",))
            if not response:
                return gotten
            if gotten[0] == response:
                return gotten

    def fcpPluginMessage(self, plugin_name, plugin_params):
        global comm
        comm.bc_to_node.put(("DEBUG", "Node fcpPluginMessage...",))
        comm.bc_to_node.put(("fcpPluginMessage", plugin_name, plugin_params,))
        ret = self.wait_for()
        comm.bc_to_node.put(("DEBUG", "Node fcpPluginMessage...returning",))
        return ret

    def _submitCmd(self, *args, **kwargs):
        global comm

        assert kwargs["async"] == False

        id, order = args
        assert order == "SubscribeUSK"
        comm.bc_to_node.put(("_submitCmd", args, kwargs,))

    def put(self, *args, **kwargs):
        global comm
        comm.bc_to_node.put(("put", args, kwargs,))
        

class FCPProtocolError(Exception):
    pass

class FCPPutFailed(Exception):
    pass

def uriIsPrivate(uri):
    return uri.startswith("USK@insert_")
