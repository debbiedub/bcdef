import NodeSimulator

def before_scenario(context, scenario):
    """Set up the simulated node."""
    context.node_simulator = NodeSimulator.get(True)

def after_scenario(context, scenario):
    context.node_simulator.shutdown()
