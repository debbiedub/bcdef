import simpy
import random


class Statement(object):
    """The statement from a participant."""
    def __init__(self, net, participant):
        self.net = net
        self.participant = participant
        self.last_block = last_block
        if self.participant in self.net.all_published_statements:
            self.net.all_published_statements[self.participant].replaced()

    def new_last_block(block_number):
        pass

    def wait_for_block(block_number):
        if self.last_block >= block_number:
            return True
        self.net.env.process


class FnetBC(object):
    """Simulating a freenet block chain.

Purpose:

 * Verify that the constants and changing of constants when certain
   things happen are fairly right.

Simplifications:

 * No verification of blocks.
 * Simplified entry.
"""
    def __init__(self):
        random.seed(42)

        self.all_published_statements = dict() # statement
        all_published_blocks = list() # of dict with the contents of the block
        all_published_blocks[0] = { "participants": {} }


    def process_node_in_chain(self, env, node_name):
        ENTRY_TIME = 200

        yield env.timeout(random.randint(1, ENTRY_TIME))
        print("Entry Done for", node_name, "at", env.now)

        while True:
            my_monitored_entrants = list()
            waiting_lists = list()
            # go through participants and create waiting lists.
            # Here is a simplified version
            my_monitored_entrants.add_all(all_published_blocks[-1]["participants"])
            
            yield AnyOf(forN, forN-1, ... for1, for0, new_block_from_any_of_my_monitored_entires, waiting time)
            if new_block:
                create_new_statement
                continue
            if others_calculate_and_wait_time:
                add_a_waiting_time
            if waiting_time_elapsed:
                create_new_block
                create_new_statement_with_the_new_block

def main():
    nodes = 2

    env = simpy.Environment()
    net = FnetBC()
    for n in range(nodes):
        env.process(net.process_node_in_chain(env, "node" + str(n)))
    env.run(until=10000)

if __name__ == "__main__":
    main()
