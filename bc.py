#!/usr/bin/env python

from fcp.node import FCPNode, DETAIL, FCPProtocolError, uriIsPrivate
from fcp.xmlobject import XMLFile
import argparse
import datetime
import logging
import os
import sys
import time
from Queue import Queue

CONTEXT = "BCDEF"
CONTENT_TYPE = "application/xml"
CACHE_DIR = "cache"

class Participants:
    """Monitor all participants and retrieve their blocks."""
    def __init__(self, node, fetcher):
        self.node = node
        self.fetcher = fetcher
        self.last_id = 0
        self.queue = Queue()

    def usk_callback(self, status, value):
        logging.debug("Participants USK-callback " +
                      str(status) + " " + str(value))
        if status != 'successful':
            return
        if value["header"] == "SubscribedUSKSendingToNetwork":
            return
        if value["header"] == "SubscribedUSKRoundFinished":
            return
        statementuri = value["URI"]
        self.fetcher.fetch(statementuri, self.fetch_callback)
        
    def validate_dom(self, dom):
        logging.warn("TODO: Add more verification on participants xml")
        return True

    def fetch_callback(self, uri, success):
        if success:
            filename = os.path.join(CACHE_DIR, toFilename(uri))
            if os.path.exists(filename):
                try:
                    dom = XMLFile(filename)
                    if not self.validate_dom(dom):
                        logging.error("Fetched " + uri + " incorrect xml.")
                        return
                    self.queue.put(dom.block_data.identity)
                except:
                    logging.error("Fetched " + uri + " invalid xml.")
            else:
                logging.error("Fetched " + uri + " without file.")

    def add_participant(self, uri):
        statementuri = toStatementURI(uri)
        self.last_id = self.last_id + 1
        id = "id_subscribeusk_" + str(self.last_id)
        self.node.node._submitCmd(id, "SubscribeUSK",
                                  URI=statementuri,
                                  Identifier=id,
                                  callback=self.usk_callback,
                                  async=True)

    def we_are_waiting(self):
        return self.last_id > 0

    def get_new_block_reference(self):
        if self.queue.empty():
            return None
        return self.queue.get(False)

    def get_last_edition_for(self, uri):
        return 0


class Blocks:
    """Block verifyer and constructor.
    Works only on blocks that are in files.
    In the first implementation, everything is in memory."""
    def __init__(self):
        self.blocks = dict()  # filename => dom
        self.verified_blocks = dict()  # filename => True or False
        self.required_data = dict()  # uri => 1

    def add_block(self, filename):
        if filename not in self.blocks:
            whole_filename = os.path.join(CACHE_DIR, filename)
            if os.path.exists(whole_filename):
                self.blocks[filename] = XMLFile(file=whole_filename)
            else:
                self.required_data[filename] = 1

    def create_block(self,
                     creator, identity, predecessor=None, number=0,
                     next_public_key=None,
                     participants=None,
                     block_chain_application=None,
                     applications=None):
        assert creator
        assert identity
        assert next_public_key
        assert participants
        assert block_chain_application
        if applications is None:
            applications = []
        root = XMLFile(root="bcdef_block")
        block_data = root.bcdef_block._addNode("block_data")
        block_data._addNode("identity")._addText(identity)
        if predecessor:
            block_data._addNode("predecessor")._addText(predecessor)
        block_data._addNode("number")._addText(str(number))
        block_data._addNode("created")._addText(datetime.datetime.utcnow().isoformat())

        creator_element = block_data._addNode("creator")
        creator_element._addNode("identity")._addText(creator)
        creator_element._addNode("next_public_key")._addText(next_public_key)
        participants_node = block_data._addNode("participants")
        seen_participant = creator
        participants_node._addNode("edition")._addText(
            str(participants.get_last_edition_for(creator)))
        pred_predecessor = predecessor
        while pred_predecessor:
            pred_block = self.blocks[predecessor]
            pred_creator = pred_block.creator
            participants_node._addNode("edition")._addText(
                participants.get_last_edition_for(pred_creator))
            pred_predecessor = pred_block.predecessor
                    
        if block_chain_application:
            block_chain_application.add(block_data)
        applications = block_data._addNode("applications")
        for application in applications:
            application.add(applications)

        return root.toxml()
        
    def _check_block(self, filename):
        "Does verification but does not store the result."
        self.add_block(filename)
        root = self.blocks[filename]
        if root.block_data.previous_block:
            previous_filename = toFilename(root.block_data.previous_block)
            previous_result = self.verify_block(previous_filename)
            if previous_result is False:
                logging.warn("Previous block did not verify for " + filename)
                return False
            if previous_result is None:
                return None
            if (root.block_data.number != 
                self.blocks[previous_filename].block_data.number + 1):
                logging.warn("Is not a successor of the previous block: " + 
                             filename)
                return False

        logging.warn("Need to add more elaborate checks to really verify " + 
                     filename)

        return True
        
                
    def verify_block(self, filename, last):
        """Verify a block.

        If it is the LAST block, do extra verifications.

        Return True if verified.
        Return False if not verified (i.e. something is wrong).
        Return None if verification is not possible. This is because
               more data needs to be fetched. The list of what needs
               to be fetched can be retrieved using required_data().
        """
        if filename in self.verified_blocks:
            return self.verified_blocks[filename]
        result = self._check_block(filename)
        if result is None:
            return None
        self.verified_blocks[filename] = result
        return result


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
    def __init__(self, node):
        self.node = node

        self.already_fetching = dict()  # uri => [callback, ...]
        self.in_cache = dict()
        self.ids = dict()  # identity => Jobticket

        if not os.path.exists(CACHE_DIR):
            os.mkdir(CACHE_DIR)
        else:
            for dirpath, dirnames, filenames in os.walk(CACHE_DIR):
                for filename in filenames:
                    self.in_cache[fromFilename(filename)] = 0

    def fetch(self, uri, callback):
        """When done, CALLBACK is called with URI and success (a boolean)."""
        if uri in self.in_cache:
            callback(uri, True)
            return
        if uri in self.already_fetching:
            self.already_fetching[uri].append(callback)
        else:
            self.already_fetching[uri] = [callback]
        ticket = self.node.node.get(uri, async=True,
                                    callback=self.callback)
        self.ids[ticket.id] = ticket
        
    def callback(self, status, value):
        logging.debug("Fetcher callback " + str(status) + " " + str(value))
        if status == "pending":
            return

        if status == 'failed':
            logging.warn("Fetched failed: " + value["CodeDescription"])
            identifier = value["Identifier"]
            uri = self.ids[identifier].uri
            for callback in self.already_fetching[uri]:
                callback(uri, False)
            self.already_fetching.pop(uri)
            self.ids.pop(identifier)
            return

        content_type, data, parameters = value
        identifier = parameters["Identifier"]
        uri = self.ids[identifier].uri

        if content_type != CONTENT_TYPE:
            logging.warn("Fetched failed on content type.")
            for callback in self.already_fetching[uri]:
                callback(uri, False)
            self.already_fetching.pop(uri)
            self.ids.pop(identifier)
            return

        logging.info("Fetched " + uri)
        open(os.path.join(CACHE_DIR, toFilename(uri)), "w").write(data)
        for callback in self.already_fetching[uri]:
            callback(uri, True)
        self.already_fetching.pop(uri)
        self.ids.pop(identifier)

        
class BCMain:
    def restart(self):
        verbosity = DETAIL
        self.node = FCPNode(verbosity=verbosity)
        logging.info("Connected to the node")

    def __init__(self, name=None):
        self.fetcher = Fetcher(self)
        self.participants = Participants(self, self.fetcher)

        self.restart()
        self._wait_for_wot()
        ownIdentity = self.WOTMessage("GetOwnIdentities")[0]
        if name is None:
            if ownIdentity["Replies.Amount"] == 1:
                index = "0"
            else:
                logging.fatal("Must specify name since your WoT does not have a single identity.")
                for i in range(ownIdentity["Replies.Amount"]):
                    logging.fatal("Available nickname: %s",
                                  ownIdentity["Replies.Nickname" + str(i)])
                sys.exit(1)
        else:
            for i in range(ownIdentity["Replies.Amount"]):
                if name == ownIdentity["Replies.Nickname" + str(i)]:
                    index = str(i)
                    break
            else:
                raise ValueError("Cannot find nickname " + name)
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
        self.blocks = Blocks()

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

    def run(self):
        identities_by_score = self.WOTMessage("GetTrustees",
                                              Context=CONTEXT,
                                              Identity=self.identity)[0]
        logging.info("Block Chain Participants: %s",
                     identities_by_score["Replies.Amount"])

        if not CONTEXT in self.contexts:
            logging.info("Joining %s for the first time.", CONTEXT)
            self.WOTMessage("AddContext",
                            Identity=self.identity,
                            Context=CONTEXT)

        # TODO: Add functions
        # Fetch participants statements, set up subscriptions for USKs
        for i in range(identities_by_score["Replies.Amount"]):
            participanturi = toRootURI(identities_by_score["Replies.RequestURI" +
                                                           str(i)])
            if participanturi == self.requesturi:
                continue
            self.participants.add_participant(participanturi)

        while self.participants.we_are_waiting():
            block_reference = self.participants.get_new_block_reference()
            if block_reference:
                self.blocks.add_block(toFilename(block_reference))
                continue
            time.sleep(10)

        # As new blocks arrive:
        # 1. Verify blocks.
        # 2. When you have a long block chain (100 or so) or when you
        #    have received information from everyone, publish your
        #    statement with the last block of the longest chain.
        # 3. Calculate when you are allowed to insert a block and do so.

        return

    def create_first_block(self):

        pub, priv = self.node.genkey()
        print priv
        print self.blocks.create_block(self.requesturi,
                                       identity=self.requesturi + "BlockChainBlock-a",
                                       next_public_key=pub, 
                                       block_chain_application=Application(),
                                       participants=self.participants)
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
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str,
                        help="Name of the user")
    parser.add_argument("--create-first-block", action="store_true",
                        help="Just create the first block.")
    args = parser.parse_args()
    bc_main = BCMain(args.name)

    if args.create_first_block:
        bc_main.create_first_block()
        return
    bc_main.run()


main()
