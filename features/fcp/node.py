import NodeSimulator

DETAIL = object()
class FCPNode(object):
    def __init__(self, verbosity):
        assert verbosity == DETAIL

    def fcpPluginMessage(self, plugin_name, plugin_params):
        assert plugin_name == "plugins.WebOfTrust.WebOfTrust"

        message = plugin_params["Message"]
        assert message in ["Ping", "GetTrustees", "AddContext", "GetOwnIdentities"]

        if message == "Ping":
            return ["Pong"]

        if message == "GetOwnIdentities":
            node_simulator = NodeSimulator.get()
            reply = {"Replies.Amount":len(node_simulator.users)}
            index = 0
            for username in node_simulator.users:
                reply["Replies.Nickname" + str(index)] = username
                reply["Replies.Identity" + str(index)] = "USK@identity_" + username + "/"
                if node_simulator.users[username].insert:
                    reply["Replies.InsertURI" + str(index)] = "USK@insert_" + username
                reply["Replies.RequestURI" + str(index)] = "USK@request_" + username
                index = index + 1
            return [reply]

        raise NotImplementedError(message)

    def _submitCmd(self, id, order, **kwargs):
        assert order == "SubscribeUSK"
        node_simulator = NodeSimulator.get()
        if kwargs["async"]:
            node_simulator.call(kwargs["callback"],
                                status='successful',
                                header="SubscribedUSK",
                                URI=kwargs["URI"])
            node_simulator.delayed_call(kwargs["callback"],
                                        status='successful',
                                        header="SubscribedUSKRoundFinished")
        else:
            raise NotImplementedError()

class FCPProtocolError(Exception):
    pass

class FCPPutFailed(Exception):
    pass

def uriIsPrivate(uri):
    return uri.startswith("USK@insert_")
