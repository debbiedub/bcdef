from multiprocessing import Queue

from fcp.CommunicationQueues import comm


@given(u'the node is running')
def step_impl(context):
    global comm
    comm.set(bc_to_node=Queue())
    comm.set(node_to_bc=Queue())


@then(u'a first block is created')
def step_impl(context):
    context.node_simulator.expect("put")
