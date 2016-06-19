#!/usr/bin/env python

from fcp.node import FCPNode, DETAIL, FCPProtocolError, uriIsPrivate
import time

CONTEXT = "BCDEF"


class Node:
    def __init__(self):
        self.restart()

    def restart(self):
        self.node = FCPNode(verbosity=DETAIL)

    def WOTMessage(self, message, **kw):
        kw["Message"] = message
        return self.node.fcpPluginMessage(plugin_name="plugins.WebOfTrust.WebOfTrust",
                                          plugin_params=kw)

    def _wait_for_wot(self):
        waiting_time = 10
        while True:
            try:
                return self.WOTMessage("Ping")
            except FCPProtocolError:
                self.node.shutdown()
                self.node = None
                print "Can't find WebOfTrust. Will retry after", str(waiting_time) + "s."
                time.sleep(waiting_time)
                waiting_time += 10
                self.restart()

    def run(self):
        self._wait_for_wot()
        ownIdentity = self.WOTMessage("GetOwnIdentities")[0]
        assert ownIdentity["Replies.Amount"] == 1
        print "You are:", ownIdentity["Replies.Nickname0"]

        participants = self.WOTMessage("GetIdentitiesByScore",
                                       Context=CONTEXT, Selection="+")[0]
        print "Block Chain Participants:", participants["Replies.Amount"]

        # print "(Sone Participants:",
        # print str(self.WOTMessage("GetIdentitiesByScore",
        #                           Context="Sone",
        #                           Selection="+")[0]["Replies.Amount"]) + ")"

        own_is_participant = False
        for p in range(100):
            cp = "Replies.Contexts0.Context" + str(p)
            if cp in ownIdentity:
                if ownIdentity[cp] == CONTEXT:
                    own_is_participant = True
            else:
                break

        if not own_is_participant:
            print "Joining", CONTEXT, "for the first time."
            self.WOTMessage("AddContext",
                            Identity=ownIdentity["Replies.Identity0"],
                            Context=CONTEXT)

        insertURI = ownIdentity["Replies.InsertURI0"].split("/WebOfTrust/")[0] + "/"
        assert uriIsPrivate(insertURI)

        print "Inserting Block"
        br = self.node.put(uri='SSK' + insertURI[3:] + "BlockChainBlock-a",
                           data="some data in the block",
                           mimetype="application/xml",
                           priority=2,
                           Verbosity=9)
        print br
        uri = br
        print "Inserting Statement"
        r = self.node.put(uri=insertURI + "BlockChainStatement/0/contents.xml",
                          data="some data: " + uri,
                          mimetype="application/xml",
                          priority=2,
                          Verbosity=9)
        print r
        print "Completed Statement"


def main():
    node = Node()
    node.run()


main()
