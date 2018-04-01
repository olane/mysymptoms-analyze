# Let's make this data fun again

So we've got our .sqlite database, and we know roughly how it works. We've had a play around with extracting some of the data, and we've seen enough to know that we're going to have to do _something_ about all the data inconsistencies otherwise we're just going to get crap data out.

## There's a few options here

### Careful SQL (our approach so far)

We could continue to carefully inspect all of our queries, check and double check the results, and tweak them to make sure they all take into account the fact that there could be duplicates and edge cases that trip us up unless we special-case them.

Pros:
- We've done some of the work already
- SQL is pretty good at things like deduplication of data sets
- The app works (mostly), right? It must be using a fair bit of SQL under the hood to retrieve/save this stuff, so it seems fairly likely this approach could succeed

Cons:
- Multiple queries agains the same tables will all need hardening against the same edge cases. It ain't gonna be very DRY.
- We might be fixing edge cases that only exist data we don't actually care about (like items that have never been used in an event, for example)
- It's really hard to know if weird query results have been caused by inconsistent data or a buggy query!

### Head in the sand

We could ignore all (or many) of the inconsistencies until we come to actually do some data processing/analysis, at which point we could write some stuff to do some deduplication.

Pros:
- I don't have to think about anything yet

Cons:
- It's going to be _even harder_ to know if data problems existed to start off with or have been introduced in the pipeline
- We'll probably have to fall back to one of the other approaches at some point anyway - the data might be broken in ways that mean we can't fix it at the end of the pipeline

### Rip the bandaid off

We could massage the data now to try to get it as consistent as possible.

Pros:
- It makes the whole rest of the process way easier if we can make more assumptions about the integrity of the data
- We can delete any data we know we're not interested in, and with it any edge cases lurking within
- Relational databases are really good at _guaranteeing_ integrity constraints, so it makes sense to do our cleaning up while the data is still in a database

Cons:
- We could accidentally delete something important and not notice (deleting something important but noticing is fine - we'll keep the full dataset around anyway)


I think this option is the only real option.

## Let's get scrubbing


