import os

from bc import Participants, CACHE_DIR, toFilename, toParticipant


class FCPNode(object):
    def _submitCmd(self, *args, **kwargs):
        kwargs["callback"]("successful",
                           {"header":"Found" + kwargs["URI"],
                            "URI":"FOUNDURI" + kwargs["URI"]})


class Node(object):
    def __init__(self):
        self.node = FCPNode()


class Fetcher(object):
    def fetch(self, uri, callback):
        if not os.path.exists(CACHE_DIR):
            os.mkdir(CACHE_DIR)
        open(os.path.join(CACHE_DIR, toFilename(uri)), "w").write("contents")
        callback(uri=uri, success=False)
        callback(uri=uri, success=True)


@given(u'there are no participants')
def step_impl(context):
    context.tested_object = Participants(Node(), Fetcher())

@when(u'a participant is added')
def step_impl(context):
    context.tested_object.add_participant("URI")

@then(u'a block is found')
def step_impl(context):
    assert context.tested_object.get_new_block_reference()

@given(u'one participant with a block')
def step_impl(context):
    context.tested_object = Participants(Node(), Fetcher())
    context.tested_object.add_participant("URI")
    assert context.tested_object.get_new_block_reference()

@when(u'another participant is added')
def step_impl(context):
    context.tested_object.add_participant("URI2")

@then(u'a new block is not found')
def step_impl(context):
    assert not context.tested_object.get_new_block_reference()

@then(u'there is one participant')
def step_impl(context):
    assert 1 == len(list(context.tested_object.get_participants()))

@then(u'there are two participants')
def step_impl(context):
    assert 2 == len(list(context.tested_object.get_participants()))
