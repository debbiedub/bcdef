from bc import BCMain

@when(u'the application is started to create the first block')
def step_impl(context):
    BCMain("Me").create_first_block()

