#!/usr/bin/env python

from fcp.node import FCPNode, DETAIL, FCPProtocolError, uriIsPrivate, \
    FCPPutFailed
from fcp.xmlobject import XMLFile
from xml.parsers.expat import ExpatError
import argparse
import datetime
import logging
import os
import sys
import time
import random
from Queue import Queue

CONTEXT = "BCDEF"
CONTENT_TYPE = "application/xml"
CACHE_DIR = "cache"


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
                    self.in_cache[fromFilename(filename)] = 1

    def fetch(self, uri, callback):
        """When done, CALLBACK is called with URI and success (a boolean)."""
        if uri in self.in_cache:
            callback(uri, True)
            return
        if uri in self.already_fetching:
            self.already_fetching[uri].append(callback)
        else:
            self.already_fetching[uri] = [callback]
            ticket = self.node.node.get(uri, async=True, priority=1,
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
        self.in_cache[uri] = 1

    def blocking_fetch(self, uri):
        """Same as fetch except that we block until it succeeds.

        If the data is not found, an exception is thrown (from lower level)."""
        if uri in self.in_cache:
            return uri
        result = self.node.node.get(uri, async=False, priority=1)
        content_type, data, parameters = result
        if content_type != CONTENT_TYPE:
            raise RuntimeError("Incorrect content_type")
        open(os.path.join(CACHE_DIR, toFilename(uri)), "w").write(data)
        return uri

    def blocking_get_dom(self, uri):
        return XMLFile(path=os.path.join(CACHE_DIR, toFilename(blocking_fetch(uri))))


class Participants:
    """Monitor all participants and retrieve their blocks."""
    def __init__(self, node, fetcher):
        self.node = node
        self.fetcher = fetcher
        self.last_id = 0
        self.queue = Queue()
        self.last_file = dict()
        self.round_finished = Queue(maxsize=1)
        self.round_timeout = None
        self.random = random.Random()

    def usk_callback(self, status, value):
        logging.debug("Participants USK-callback " +
                      str(status) + " " + str(value))
        if status != 'successful':
            return
        if value["header"] == "SubscribedUSK":
            return
        if value["header"] == "SubscribedUSKSendingToNetwork":
            return
        if value["header"] == "SubscribedUSKRoundFinished":
            if not self.round_finished.full():
                self.round_finished.put(1, block=False)
            return
        # if value["NewKnownGood"] != "true":
        #    return
        uri = value["URI"]
        self.fetcher.fetch(uri, self.fetch_callback)
        
    def validate_dom(self, dom):
        logging.warn("TODO: Add more verification on participants xml")
        return True

    def fetch_callback(self, uri, success):
        if success:
            filename = os.path.join(CACHE_DIR, toFilename(uri))
            if os.path.exists(filename):
                self.last_file[toParticipant(uri)] = filename
                try:
                    dom = XMLFile(path=filename)
                    if not self.validate_dom(dom):
                        logging.error("Fetched " + uri + " incorrect xml.")
                        return
                    self.queue.put(dom.bcdef_participant.block_data.identity._text)
                except ExpatError:
                    logging.error("Fetched " + uri + " invalid xml.")
                except AttributeError:
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
                                  priority=1,
                                  callback=self.usk_callback,
                                  async=True)

    def we_are_waiting(self):
        return self.last_id > 0

    def wait_for_round(self):
        while not self.round_finished.empty():
            self.round_finished.get()
        logging.debug("Waiting for round...")
        ret = self.round_finished.get(timeout=self.round_timeout)
        logging.debug("Waiting for round...completed.")
        return ret

    def get_new_block_reference(self):
        if self.queue.empty():
            return None
        return self.queue.get(False)

    def get_participants(self):
        for participant in self.last_file:
            yield participant

    def get_last_for(self, participant):
        """Return edition and random."""
        last = self.last_file[participant]
        try:
            random = int(XMLFile(last).block_data.participant.random)
        except:
            random = None
        return (edition_for(fromFilename(last)), random)

    def create_statement(self,
                         creator,
                         block, number,
                         application=None):
        assert creator
        assert block
        assert number
        if application is None:
            application = Application()

        root = XMLFile(root="bcdef_participant")

        bcdef_participant = root.bcdef_participant
        participant = bcdef_participant._addNode("participant")
        participant._addNode("identity")._addText(creator)
        participant._addNode("edition")._addText(
            str(1 + self.get_last_for(creator)[0]))
        participant._addNode("random")._addText(
            str(int(self.random.randint(1, 8000000000000000000))))

        block_data = bcdef_participant._addNode("block_data")
        block_data._addNode("identity")._addText(block)
        block_data._addNode("number")._addText(str(number))

        applications = bcdef_participant._addNode("applications")
        for application in applications:
            application.add(applications)

        return root.toxml()


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
                self.blocks[filename] = XMLFile(path=whole_filename)
            else:
                self.required_data[filename] = 1

    BLOCK_NUMBER_DIGITS = "abcdefghijkmnopqrstuvwxyz"

    def _next_block_number(self, block_number):
        if not block_number:
            return self.BLOCK_NUMBER_DIGITS[0]
        pos = self.BLOCK_NUMBER_DIGITS.find(block_number[-1])
        prefix = block_number[:-1]
        next_pos = pos + 1
        if next_pos >= len(self.BLOCK_NUMBER_DIGITS):
            next_pos = 0
            prefix = self._next_block_number(prefix)
        return prefix + self.BLOCK_NUMBER_DIGITS[next_pos]

    def find_next_block_number(self):
        filename = os.path.join(CACHE_DIR, "my_last_block_number.txt")
        if os.path.exists(filename):
            last = open(filename).read()
        else:
            last = ""
        next_block_number = self._next_block_number(last)
        open(filename, "w").write(next_block_number)
        return next_block_number

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
        creator_node = participants_node._addNode("participant")
        creator_node._addNode("identity")._addText(creator)
        creator_node._addNode("edition")._addText(
            str(1 + participants.get_last_for(creator)[0]))
        if predecessor:
            for participant in self.blocks[predecessor].block_data.participants:
                if participant.identity == creator:
                    continue
                edition, random = participants.get_last_for(participant)
                participant_node = participants_node._addNode("participant")
                participant_node._addNode("identity").addText(creator)
                participant_node._addNode("edition")._addText(str(edition))
                participant_node._addNode("random")._addText(str(random))
                    
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
        if hasattr(root.bcdef_block.block_data, "previous_block"):
            previous_filename = toFilename(root.bcdef_blockblock_data.previous_block._text)
            previous_result = self.verify_block(previous_filename)
            if previous_result is False:
                logging.warn("Previous block did not verify for " + filename)
                return False
            if previous_result is None:
                return None
            if (int(root.bcdef_block.block_data.number._text) != 
                self.blocks[previous_filename].block_data.number + 1):
                logging.warn("Is not a successor of the previous block: " + 
                             filename)
                return False

        logging.warn("Need to add more elaborate checks to verify every block.")

        return True
        
                
    def verify_block(self, filename, last):
        """Verify a block.

        If it is the LAST block, do extra verifications.

        Return True if verified.
        Return False if not verified (i.e. something is wrong).
        Return None if verification is not possible. This is because
               more data needs to be fetched. The list of what needs
               to be fetched can be retrieved using get_required_data().
        """
        if filename in self.verified_blocks:
            return self.verified_blocks[filename]
        result = self._check_block(filename)
        if result is None:
            return None
        self.verified_blocks[filename] = result
        return result

    def get_required_data():
        try:
            return self.required_data.keys()
        finally:
            self.required_data = dict()


class Application:
    def add(self, node):
        pass


def toRootURI(uri):
    return uri.split("/WebOfTrust/")[0] + "/"


def toStatementURI(uri, index=0):
    return uri + "BlockChainStatement/" + str(index)


def edition_for(uri):
    return int(uri.split("/")[-1])


def toParticipant(uri):
    return uri.split("/BlockChainStatement/")[0] + "/"


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

        self.participants.add_participant(self.requesturi)
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

    def verify_whole_blockchain(self):
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

        # 1. Fetch entire block chain:
        logging.info("1.a Fetch participants from WoT")
        for i in range(identities_by_score["Replies.Amount"]):
            participanturi = toRootURI(identities_by_score["Replies.RequestURI" +
                                                           str(i)])
            if participanturi == self.requesturi:
                continue
            self.participants.add_participant(participanturi)

        logging.info("1.b Get a block reference.")
        block_reference = None
        while self.participants.we_are_waiting():
            block_reference = self.participants.get_new_block_reference()
            if block_reference:
                break
            self.participants.wait_for_round()
            block_reference = self.participants.get_new_block_reference()
            if block_reference:
                break
            # We didn't get anything.
            logging.info("Round finished without result. " +
                         "Use an old block if all participants agree.")
            block_reference = None
            for participant in self.participants.get_participants():
                edition = self.participants.get_last_for(participant)[0]
                statement_uri = toStatementURI(participant, edition)
                dom = self.fetcher.blocking_get_dom(statement_uri)
                br = dom.bcdef_participant.participant.block_data.identity._text

                if not block_reference:
                    block_reference = br
                    continue
                if block_reference != br:
                    logging.info("Not all participants agree on the block")
                    block_reference = None
                    break
            if block_reference:
                break
            time.sleep(10)

        if not block_reference:
            logging.error("Could not find block.")
            return

        logging.info("1.c Fetch the block " + block_reference + " " +
                     "and all its predecessors.")
        uri = self.fetcher.blocking_fetch(block_reference)
        whole_block_chain_fetched = False
        while not whole_block_chain_fetched:
            result = self.blocks.verify_block(toFilename(uri), last=True)
            if result == False:
                logging.warn("Block " + block_reference + " did not verify.")
                block_reference = self.participants.get_new_block_reference()
                if block_reference:
                    logging.info("Attempting another block reference.")
                    uri = self.fetcher.blocking_fetch(block_reference)
                    continue
                raise RuntimeException("Block does not verify: " + uri)
            if result == True:
                whole_block_chain_fetched = True
            if result is None:
                logging.debug("Download more info to verify")
                for required in self.blocks.get_required_data():
                    self.fetcher.blocking_fetch(required)
        logging.info("Whole block chain verified")

    def run(self):
        self.verify_whole_blockchain()
        logging.info("2. Open wiki.")
        logging.error("Not implemented yet.")
        while True:
            logging.info("3.a Publish own statement.")
            logging.error("Not implemented yet.")
            logging.info("3.b Wait for statement updates.")
            logging.error("Not implemented yet.")
            logging.info("3.b.1. If a new statement arrives download it.")
            logging.error("Not implemented yet.")
            logging.info("3.b.2. If the statement contained a new block, download it. Verify it and restart from 3.a.")
            logging.error("Not implemented yet.")
            logging.info("3.b.3. If the statement was from one of our monitored participants recalculate if we can create a block.")
            logging.error("Not implemented yet.")
            logging.info("3.b.4. If so, create a block, upload a new statement with the new block.")
            logging.error("Not implemented yet.")
            break

        return

    def create_first_block(self):
        self.participants.wait_for_round()

        number = 1

        pub, priv = self.node.genkey()
        open(os.path.join(CACHE_DIR, "private_key_" + str(number)),
             "w").write(priv)

        block_number = self.blocks.find_next_block_number()
        waiting_time = 2

        while True:
            try:
                block = self.blocks.create_block(self.requesturi,
                                                 identity=(self.requesturi +
                                                           "BlockChainBlock-" +
                                                           block_number),
                                                 number=number,
                                                 next_public_key=pub,
                                                 block_chain_application=Application(),
                                                 participants=self.participants)

                logging.info("Inserting Block " + block_number)
                br = self.node.put(uri=('SSK' + self.inserturi[3:] +
                                        "BlockChainBlock-" + block_number),
                                   data=block,
                                   mimetype="application/xml",
                                   priority=2,
                                   Verbosity=9)
                logging.info("Inserted Block " + br)
                uri = br
                break
            except FCPPutFailed:
                block_number = self.blocks.find_next_block_number()
                self.node.shutdown()
                self.node = None
                logging.warn("Will retry after %ds.", waiting_time)
                time.sleep(waiting_time)
                waiting_time += 10
                self.restart()

        logging.info("Inserting Statement")
        my_edition = 1 + int(self.participants.get_last_for(self.requesturi)[0])
        r = self.node.put(uri=toStatementURI(self.inserturi, my_edition),
                          data=self.participants.create_statement(self.requesturi,
                                                                  uri,
                                                                  number),
                          mimetype="application/xml",
                          priority=2,
                          Verbosity=9)
        logging.info("Inserted Statement " + r)


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


if __name__ == '__main__':
    main()
