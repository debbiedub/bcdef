import logging
from multiprocessing import Process

from bc import BCMain
from fcp.CommunicationQueues import comm


def run_create_first_block(queues, *args):
    global comm
    comm.set(queues=queues)
    try:
        logging.getLogger().setLevel(logging.DEBUG)
        # logging.getLogger().addHandler(comm.get_handler())
        logging.info("Started logging")
        bc = BCMain(*args)
        bc.participants.round_timeout = 1
        bc.create_first_block()
    finally:
        comm.empty_queues()


@when(u'the application is started to create the first block')
def step_impl(context):
    global comm
    context.bc_process = Process(target=run_create_first_block,
                                 args=(comm, "Me",))
    context.bc_process.start()

    context.node_simulator.expect("hello")
    context.node_simulator.respond(("olleh",))

    context.node_simulator.expect_wot("Ping")
    context.node_simulator.respond_wot({"Message":"Pong"})
    context.node_simulator.expect_wot("GetOwnIdentities")
    context.node_simulator.respond_wot({"Replies.Amount": "0"})
