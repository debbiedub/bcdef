---
layout: page
title: Purpose
permalink: /purpose/
---

The purpose of having a block chain in freenet is to provide Freenet
with a mechanism that can be used to establish a common truth that is
modifyable.  The typical application for this is a wiki, editable by
anyone.

A common truth can have many forms such as:

- A single resources.
- One resource per participating user.
- Many common resources.

## Single Resource

The single resource is where the common truth at each point in time
consists of a single URI. The URI can change. The block chain will
make sure that throughout freenet everyone agrees what the truth
is. This is best compared with the [The Filtered
Index](/USK@ozMQYaCEXnlHQQggITYSIeNSxqdMknqjOIYyCdMKqJA,gJyID9FRxaM5zDql3D8-wHACAusOYa5Aag3M4tSEt~g,AQACAAE/Index/1220/)
or
[TPI](/USK@Jd5ohLRviSl~HgXdjMGLSkiX2uce8-18MH5bSt4QaoM,UITsohvo1NYZQR3BYBeTbpmBHpunKj6h7Kt0KNogw1c,AQACAAE/index/993/). The
benefit of using a block chain for this is that there is no need of
sharing keys. Everyone can use their own keys to publish and
publishers that misbehave can be identified and their changes can be
reverted and they can be ignored.

## One Resource per Participating User

This provides a way to allow applications to publish information from
many users to many users without the need of having all users monitor
all USKs. Because of the design of the block chain, the information
can propagate quickly in the network while each participant monitors a
limited set of USKs. This is useful when there is a large set of users
that is not very active. This is best compared with the way
information propagates in fms and sone.

## Many common resources

Many common resources is just as the single resource except that the
information is split on many sites indexed in some way.  Typically a
wiki where each page is indexed by its name.
