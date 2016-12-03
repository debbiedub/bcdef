import os

from bc import Participants, CACHE_DIR, toFilename


class FCPNode(object):
    def _submitCmd(self, *args, **kwargs):
        kwargs["callback"]("successful",
                           {"header":"FoundURI", "URI":"FOUNDURI"})


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

@then(u'a block is found.')
def step_impl(context):
    assert context.tested_object.get_new_block_reference()
