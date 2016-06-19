#!/usr/bin/env python

from fcp.node import FCPNode, DETAIL, FCPProtocolError, uriIsPrivate
from fcp.xmlobject import XMLFile
import time
import datetime

CONTEXT = "BCDEF"

class Participants():
    def add(self, node):
        pass

class Application():
    def add(self, node):
        pass

class Node:
    def restart(self):
        self.node = FCPNode(verbosity=DETAIL)

    def __init__(self):
        self.restart()
        self._wait_for_wot()
        ownIdentity = self.WOTMessage("GetOwnIdentities")[0]
        assert ownIdentity["Replies.Amount"] == 1
        self.nickname = ownIdentity["Replies.Nickname0"]
        self.identity = ownIdentity["Replies.Identity0"]
        self.inserturi = ownIdentity["Replies.InsertURI0"].split("/WebOfTrust/")[0] + "/"
        self.requesturi = ownIdentity["Replies.RequestURI0"].split("/WebOfTrust/")[0] + "/"

        self.contexts = []
        for p in range(100):
            cp = "Replies.Contexts0.Context" + str(p)
            if cp in ownIdentity:
                self.contexts.append(ownIdentity[cp])
            else:
                break

        print "You are:", self.nickname

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

    def create_block(self,
                     identity="a", predecessor=None, number=0,
                     next_public_key=None,
                     participants=None,
                     block_chain_application=None,
                     applications=None):
        assert next_public_key
        assert participants
        assert block_chain_application
        if applications is None:
            applications = []
        root = XMLFile(root="bcdef_block")
        block_data = root.bcdef_block._addNode("block_data")
        block_data._addNode("identity")._addText(self.requesturi +
                                                 "BlockChainBlock-" + identity)
        if predecessor:
            block_data._addNode("predecessor")._addText(predecessor)
        block_data._addNode("number")._addText(str(number))
        block_data._addNode("created")._addText(datetime.datetime.utcnow().isoformat())
        creator = block_data._addNode("creator")
        creator._addNode("identity")._addText(self.requesturi)
        creator._addNode("next_public_key")._addText(next_public_key)
        if participants:
            participants.add(block_data._addNode("random_participants"))
        if block_chain_application:
            block_chain_application.add(block_data)
        applications = block_data._addNode("applications")
        for application in applications:
            application.add(applications)

        return root.toxml()
        

    def run(self):
        pub, priv = self.node.genkey()
        print priv
        print self.create_block(identity="a", next_public_key=pub, 
                                block_chain_application=Application(),
                                participants=Participants())
        return

        participants = self.WOTMessage("GetIdentitiesByScore",
                                       Context=CONTEXT, Selection="+")[0]
        print "Block Chain Participants:", participants["Replies.Amount"]

        if not CONTEXT in self.contexts:
            print "Joining", CONTEXT, "for the first time."
            self.WOTMessage("AddContext",
                            Identity=self.identity,
                            Context=CONTEXT)

        insertURI = self.inserturi
        assert uriIsPrivate(insertURI)

        print "Inserting Block"
        br = self.node.put(uri='SSK' + insertURI[3:] + "BlockChainBlock-b",
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
