from multiprocessing import Process

from bc import BCMain
from fcp.CommunicationQueues import comm


def run(queues, *args):
    global comm
    comm.set(queues=queues)
    try:
        bc = BCMain(*args)
        bc.participants.round_timeout = 1
        bc.create_first_block()
    finally:
        comm.empty_queues()


@when(u'the application is started to create the first block')
def step_impl(context):
    global comm
    context.bc_process = Process(target=run, args=(comm, "Me",))
    context.bc_process.start()

    context.node_simulator.expect("hello")
    context.node_simulator.respond("olleh")

    context.node_simulator.expect("fcpPluginMessage")
    context.node_simulator.respond("me")
    context.node_simulator.expect("subscribe")
    context.node_simulator.expect("loop")
