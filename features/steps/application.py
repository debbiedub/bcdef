from bc import BCMain

@when(u'the application is started to create the first block')
def step_impl(context):
    bc = BCMain("Me")
    bc.participants.round_timeout = 1
    bc.create_first_block()

