from NodeSimulator import NodeSimulator

def before_scenario(context, scenario):
    """Set up the simulated node."""
    context.node_simulator = NodeSimulator()
