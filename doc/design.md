---
layout: page
title: Design
permalink: /design/
---

BCDEF implements the block chain.  BCDEF is a fred plugin.  It
provides an API programmatically and over FCP.  Applications using the
API can
- store information on the block chain,
- verify new information on the block chain accepting or rejecting and,
- get information stored on the block chain.

Application data is stored on the block chain.  Verification of the
application data is on a higher level than the verification of the
block chain integrity.  The block chain is used to communicate the
result of the verification.

Each block is an SSK that is a splitfile with files according to
certain rules.

There is a size limit on the transaction provided by each application
in order to make it possible to create blocks that are small enough to
be handled well by freenet.  I think the recommended size is less than
2M so a good limit would probably be around 500k to guarantee room for
at least three transactions in each block.  It is assumed that most of
the transactions is just on or a handful of URIs so this should not be
a problem.

The BCDEF plugin adds blocks to the block chain and verifies the
integrity of the block chain.

A mix between Proof of Storage and Proof of Elapsed Time is used to
decide who is allowed to create a new block and allow everyone to
verify that block.
