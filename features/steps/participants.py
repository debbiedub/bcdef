import os

from bc import Participants
from fcp.xmlobject import XMLFile

class FCPNode(object):
    def _submitCmd(self, *args, **kwargs):
        kwargs["callback"]("successful",
                           {"header":"Found" + kwargs["URI"],
                            "URI":"FOUNDURI" + kwargs["URI"]})


class Node(object):
    def __init__(self):
        self.node = FCPNode()


class Fetcher(object):
    def __init__(self, cache):
        self.cache = cache

    def fetch(self, uri, callback):
        self.cache.write_uri(uri, "contents")
        callback(uri=uri, success=False)
        callback(uri=uri, success=True)


class Cache(object):
    def __init__(self):
        self.contents = dict()

    def write_uri(self, uri, contents):
        self.contents[uri] = contents

    def get_uri(self, uri):
        return XMLFile(contents=self.contents[uri])


@given(u'there are no participants')
def step_impl(context):
    cache = Cache()
    context.tested_object = Participants(Node(), Fetcher(cache), cache)

@when(u'a participant is added')
def step_impl(context):
    context.tested_object.add_participant("URI")

@then(u'a block is found')
def step_impl(context):
    assert context.tested_object.get_new_block_reference()

@given(u'one participant with a block')
def step_impl(context):
    cache = Cache()
    context.tested_object = Participants(Node(), Fetcher(cache), cache)
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
