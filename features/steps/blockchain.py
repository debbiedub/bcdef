@given(u'no user exists')
def step_impl(context):
    assert not context.node_simulator.users

@given(u'there are other blockchain users')
def step_impl(context):
    context.node_simulator.add_user("Adam")
    context.node_simulator.add_user("Bill")
    context.node_simulator.add_user("Charlie")

@given(u'the blockchain exists')
def step_impl(context):
    context.node_simulator.add_block(1)

