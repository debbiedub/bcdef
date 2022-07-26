---
layout: post
title:  Calculations for scaling to a million users
tags: advocacy
---

Trying to convince myself that this project is worthwile I will do
some simple calculations on how a typical forum/microblog application
will have to behave designed with and without the block list. The
typical application has many users that can publish and read the
contents.

The ad.hoc. design used for this is that each user has some set of
data published, that changes whenever something is published and that
all other users must monitor those changes. For Sone, this data is an
USK that is changed. For FMS this data is a set of SSKs, created
daily. The overall amount of monitoring of changes grows with the
square of the amount of users.

In the block chain design, all data is published on the block chain,
and every participant monitors the block chain and publishes the block
chain head. This has the drawback of having to publish to freenet just
to maintain the block chain but allows for just monitoring a few other
users. The overall amount of monitoring of changes is designed by the
block chain mechanism. I have a certain algorithm in mind for this
where the amount of monitoring grows with the log of the amount of
users.

Resulting amount of monitoring required in the two cases

| # users   | Non-BC mon/user | Non-BC mon   | BC mon/user | BC mon      |
| --------: | --------------: | -----------: | ----------- | ----------: |
| 10        | 10              | 100          | 6 -> 10     | 60          |
| 100       | 100             | 10000        | 13 -> 91    | 1300        |
| 1000      | 1000            | 1 million    | 19 -> 190   | 19000       |
| 10000     | 10000           | 100 million  | 26 -> 351   | 260000      |
| 100000    | 100000          | 10 billion   | 33 -> 561   | 3.3 million |
| 1 million | 1 million       | 1000 billion | 39 -> 780   | 39 million  |

The BC mon/user is immediately after a new block is found and a little
less than the same amount is then added every half-hour until a new
block is created and it could grow to half of the square of the amount.
