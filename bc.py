#!/usr/bin/env python

from fcp.node import FCPNode, DETAIL, FCPProtocolError, uriIsPrivate
from fcp.xmlobject import XMLFile
import argparse
import datetime
import logging
import os
import sys
import time

CONTEXT = "BCDEF"
CONTENT_TYPE = "application/xml"

class Participants:
    def add(self, node):
        pass


class Application:
    def add(self, node):
        pass


def toRootURI(uri):
    return uri.split("/WebOfTrust/")[0] + "/"


def toStatementURI(uri):
    return uri + "BlockChainStatement/0"


def toFilename(uri):
    return (uri.
            replace("_", " ").
            replace(":", "__c").
            replace("/", "__s").
            replace(" ", "__u"))

def fromFilename(filename):
    return (filename.
            replace("__u", " ").
            replace("__s", "/").
            replace("__c", ":").
            replace(" ", "_"))


class Fetcher:
    """Keeps track of all fetched URI:s and the cache."""
    CACHE_DIR = "cache"
    def __init__(self, node):
        self.node = node

        self.already_fetching = dict()
        self.in_cache = dict()
        self.waiting_for = dict()  # id => JobTicket

        if not os.path.exists(self.CACHE_DIR):
            os.mkdir(self.CACHE_DIR)
        else:
            for dirpath, dirnames, filenames in os.walk(self.CACHE_DIR):
                for filename in filenames:
                    self.in_cache[fromFilename(filename)] = 0

    def assert_fetching(self, uri):
        """Assert that we are fetching the uri."""
        if uri in self.in_cache:
            return
        if uri in self.already_fetching:
            return
        self.already_fetching[uri] = 1
        ticket = self.node.node.get(uri, async=True,
                                    callback=self.callback)
        self.waiting_for[ticket.id] = ticket

    def callback(self, status, value):
        print value
        print self.waiting_for
        if status == 'failed':
            logging.warn("Failed to get " + value["URI"])
            return
        if status != 'successful':
            return
        content_type, contents, parameters = value
        if content_type != CONTENT_TYPE:
            logging.warn("Received strange data " + content_type + ". " +
                         "Ignoring.")
            return
        id = parameters["Identifier"]
        uri = self.waiting_for[id].uri
        open(os.path.join(self.CACHE_DIR, toFilename(uri)), "w").write(contents)

    def wait(self):
        while len(self.waiting_for):
            for ticket in self.waiting_for:
                if self.waiting_for[ticket].isComplete():
                    self.waiting_for.pop(ticket)
                    break
            time.sleep(1)
        self.already_fetching.clear()

        
class Node:
    def restart(self):
        verbosity = DETAIL
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
        self.inserturi = toRootURI(ownIdentity["Replies.InsertURI" + index])
        assert uriIsPrivate(self.inserturi)
        self.requesturi = toRootURI(ownIdentity["Replies.RequestURI" + index])

        self.contexts = []
        for p in range(100):
            cp = "Replies.Contexts" + index + ".Context" + str(p)
            if cp in ownIdentity:
                self.contexts.append(ownIdentity[cp])
            else:
                break

        logging.info("You are: %s", self.nickname)

        self.fetcher = Fetcher(self)


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

        # TODO: Add functions
        # Fetch participants statements, set up subscriptions for USKs
        waiting_for = []
        already_fetching = []
        for i in range(participants["Replies.Amount"]):
            participanturi = toRootURI(participants["Replies.Identities." +
                                                    str(i) +
                                                    ".RequestURI"])
            statementuri = toStatementURI(participanturi)
            self.fetcher.assert_fetching(statementuri)

        self.fetcher.wait()
        return
        

        # As new blocks arrive:
        # 1. Verify blocks.
        # 2. When you have a long block chain (100 or so) or when you
        #    have received information from everyone, publish your
        #    statement with the last block of the longest chain.
        # 3. Calculate when you are allowed to insert a block and do so.


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
        r = self.node.put(uri=toStatementURI(self.inserturi),
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
