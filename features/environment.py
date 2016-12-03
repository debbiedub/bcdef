import os
import shutil
from multiprocessing import Queue

from fcp.NodeSimulator import NodeSimulator
from fcp.CommunicationQueues import comm


def before_scenario(context, scenario):
    context.node_simulator = NodeSimulator()
    if os.path.exists("cache"):
        shutil.rmtree("cache")


def after_scenario(context, scenario):
    """Take down the tested object."""
    global comm
    comm.node_to_bc.put("SHUTDOWN")

    if hasattr(context, "bc_process"):
        context.bc_process.join(5)
        context.bc_process.terminate()
        context.bc_process.join()
        context.bc_process = None
    
    comm.empty_queues()
    print(scenario, "done.")
