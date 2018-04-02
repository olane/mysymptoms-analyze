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

First step: 
```console
$ cp mySymptoms.sqlite mySymptoms_scrubbed.sqlite
```

### Get rid of anything that's deleted

```sql
DELETE
FROM ingested
WHERE deleted != 0;

DELETE
FROM reactionevent
WHERE deleted != 0;
```

### Get rid of duplicates (as much as possible)

We really need to deal with all the entries in `ingested` that have the same uuid.

```sql
DELETE FROM ingested WHERE _id NOT IN (
	SELECT
		min(_id)
	FROM ingested
	GROUP BY uuid
);
```

This deletes all but the first row in the table matching a particular uuid, taking advantage of the fact that there _is_ a unique `_id` field on the table which we can use to differentiate the otherwise identical rows.

Before writing this I verified that all rows in the database with the same uuid are also the same in all the other rows that matter (although one pair varies by casing on `name`).

The same thing needs to happen on the `ingestedtoingested` table:

```sql
DELETE FROM ingestedtoingested WHERE _id NOT IN (
	SELECT 
	min(_id)
	FROM ingestedtoingested
	GROUP BY 
	    ingestedparentuuid,
	    ingestedchilduuid
);
```

### Get rid of any items not referenced

```sql

DELETE
FROM ingested 
WHERE uuid NOT IN 
	(SELECT ingestedchilduuid FROM ingestedtoingested WHERE ingestedchilduuid IS NOT NULL)
AND uuid NOT IN
	(SELECT baseitem FROM ingested WHERE baseitem IS NOT NULL)
AND uuid NOT IN
	(SELECT ingesteduuid FROM ingestedtoingestedtype WHERE ingesteduuid IS NOT NULL)
AND uuid NOT IN
	(SELECT ingesteduuid FROM ingesteddetail)
AND numberofingestedevents = 0
AND frequency = 0;

DELETE 
FROM ingestedtoingested
WHERE ingestedparentuuid NOT IN (SELECT uuid FROM ingested)
OR ingestedchilduuid NOT IN (SELECT uuid FROM ingested);
```

If you run this mutiple times, it keeps deleting things! That's actually expected - as we delete items, we get rid of references to other items, so more items can be pruned. When we put this into a script, I'll run it in a loop until it doesn't delete any rows. In the case of my database, after about 6 runs the row counts stop changing.

After this, I've only got 770 items in my `ingested` table, down from about 3.5k.


### Get rid of any reactions that belong to reaction events that don't exist

Because the reaction events table is more sensible and appears to have all its foreign keys intact, this isn't actually necessary.
```sql
DELETE FROM reaction 
WHERE reactionevent_id NOT IN (SELECT _id FROM reactionevent);
```

### Let's just double check we haven't deleted any items that are referenced by an event

```sql
SELECT * 
FROM ingesteddetail
WHERE ingesteduuid NOT IN (SELECT uuid from ingested)
AND ingesteduuid != -1;

-- 0 rows returned
```

Batshit database structure reminder: `ingesteddetail` links `ingestedevent` to `ingested`, but it also attaches intensity and duration data to `ingestedevent` in which case its `ingesteduuid` is set to `-1`.