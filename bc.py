#!/usr/bin/env python

from fcp.node import FCPNode, DETAIL, FCPProtocolError, uriIsPrivate
from fcp.xmlobject import XMLFile
import argparse
import datetime
import logging
import sys
import time

CONTEXT = "BCDEF"

class Participants():
    def add(self, node):
        pass

class Application():
    def add(self, node):
        pass

class Node:
    def restart(self):
        verbosity = None
        self.node = FCPNode(verbosity=verbosity)
        logging.info("Connected to the node")

    def __init__(self, name=None):
        self.restart()
        self._wait_for_wot()
        ownIdentity = self.WOTMessage("GetOwnIdentities")[0]
        if name is None:
            if ownIdentity["Replies.Amount"] == 1:
                index = "0"
            else:
                logging.fatal("Must specify name since your WoT does not have a single identity.")
                for i in range(ownIdentity["Replies.Amount"]):
                    logging.fatal("Available identity: %s",
                                  ownIdentity["Replies.Nickname" + str(i)])
                sys.exit(1)
        else:
            for i in range(ownIdentity["Replies.Amount"]):
                if name == ownIdentity["Replies.Nickname" + str(i)]:
                    index = str(i)
                    break
            else:
                raise IllegalArgument("Cannot find name " + name)
        self.nickname = ownIdentity["Replies.Nickname" + index]
        self.identity = ownIdentity["Replies.Identity" + index]
        self.inserturi = ownIdentity["Replies.InsertURI" + index].split("/WebOfTrust/")[0] + "/"
        assert uriIsPrivate(self.inserturi)
        self.requesturi = ownIdentity["Replies.RequestURI" + index].split("/WebOfTrust/")[0] + "/"
        assert uriIsPublic(self.requesturi)

        self.contexts = []
        for p in range(100):
            cp = "Replies.Contexts" + index + ".Context" + str(p)
            if cp in ownIdentity:
                self.contexts.append(ownIdentity[cp])
            else:
                break

        logging.info("You are: %s", self.nickname)

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
                logging.warn("Can't find WebOfTrust. Will retry after %ds.",
                             waiting_time)
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
        participants = self.WOTMessage("GetIdentitiesByScore",
                                       Context=CONTEXT, Selection="+")[0]
        logging.info("Block Chain Participants: %s",
                     participants["Replies.Amount"])

        if not CONTEXT in self.contexts:
            logging.info("Joining %s for the first time.", CONTEXT)
            self.WOTMessage("AddContext",
                            Identity=self.identity,
                            Context=CONTEXT)

        pub, priv = self.node.genkey()
        print priv
        print self.create_block(identity="a", next_public_key=pub, 
                                block_chain_application=Application(),
                                participants=Participants())
        return


        logging.info("Inserting Block")
        br = self.node.put(uri='SSK' + self.inserturi[3:] + "BlockChainBlock-b",
                           data="some data in the block",
                           mimetype="application/xml",
                           priority=2,
                           Verbosity=9)
        print br
        uri = br
        loggin.info("Inserting Statement")
        r = self.node.put(uri=self.inserturi + "BlockChainStatement/0/contents.xml",
                          data="some data: " + uri,
                          mimetype="application/xml",
                          priority=2,
                          Verbosity=9)
        print r
        print "Completed Statement"


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str,
                        help="Name of the user")
    args = parser.parse_args()
    node = Node(args.name)

    node.run()


main()
