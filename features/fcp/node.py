from CommunicationQueues import comm


DETAIL = object()


def _run(node_to_bc):
    while True:
        gotten = node_to_bc.get()
        if gotten == "SHUTDOWN":
            break

        
class FCPNode(object):
    def __init__(self, verbosity):
        assert verbosity == DETAIL
        global comm
        assert comm
        assert comm.bc_to_node
        comm.bc_to_node.put(("hello",))
        self.wait_for("olleh")

        self.node_poller = Process(target=_run, args=(comm.node_to_bc,))
        self.node_poller.start()

    def wait_for(self, response):
        global comm
        assert comm
        assert comm.node_to_bc
        while True:
            gotten = comm.node_to_bc.get()
            if gotten[0] == response:
                return gotten

    def fcpPluginMessage(self, plugin_name, plugin_params):
        global comm

        assert plugin_name == "plugins.WebOfTrust.WebOfTrust"

        message = plugin_params["Message"]
        assert message in ["Ping", "GetTrustees", "AddContext", "GetOwnIdentities"]

        comm.bc_to_node.put(("fcpPluginMessage", plugin_name, plugin_params,))
        return self.wait_for("me")

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
