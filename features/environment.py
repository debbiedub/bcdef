import fcp.NodeSimulator

def before_scenario(context, scenario):
    """Set up the simulated node."""
    context.node_simulator = fcp.NodeSimulator.get(True)

def after_scenario(context, scenario):
    context.node_simulator.shutdown()
    print(scenario, "done.")
