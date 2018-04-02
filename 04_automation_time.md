# I'm sick of clicking buttons

Let's write a script to automate this scrubbing process, so that it's repeatable and easy to iterate on.

Python has some good built in SQLite support, so let's use that:

```python
import sqlite3

def deleteDeleted(connection):
    c = connection.cursor()

    c.execute('''   DELETE
                    FROM ingested
                    WHERE deleted != 0;''')
    ingestedRowsDeleted = c.rowcount
    print 'deleted {} rows from ingested (marked as deleted)'.format(ingestedRowsDeleted)

    c.execute('''   DELETE
                    FROM reactionevent
                    WHERE deleted != 0;''')
    reactionEventRowsDeleted = c.rowcount
    print 'deleted {} rows from reactionevent (marked as deleted)'.format(reactionEventRowsDeleted)

    connection.commit()
    return ingestedRowsDeleted + reactionEventRowsDeleted

def deleteDuplicates(connection):
    c = connection.cursor()

    c.execute('''   DELETE FROM ingested WHERE _id NOT IN (
                        SELECT
                            min(_id)
                        FROM ingested
                        GROUP BY uuid
                    );''')
    ingestedRowsDeleted = c.rowcount
    print 'deleted {} rows from ingested (duplicates)'.format(ingestedRowsDeleted)

    c.execute('''   DELETE FROM ingestedtoingested WHERE _id NOT IN (
                        SELECT 
                        min(_id)
                        FROM ingestedtoingested
                        GROUP BY 
                            ingestedparentuuid,
                            ingestedchilduuid
                    );''')
    ingestedToIngestedRowsDeleted = c.rowcount
    print 'deleted {} rows from ingestedtoingested (duplicates)'.format(ingestedToIngestedRowsDeleted)

    connection.commit()
    return ingestedRowsDeleted + ingestedToIngestedRowsDeleted

def deleteUnreferenced(connection):
    c = connection.cursor()

    c.execute('''   DELETE
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
                    AND frequency = 0;''')
    ingestedRowsDeleted = c.rowcount
    print 'deleted {} rows from ingested (unreferenced)'.format(ingestedRowsDeleted)

    c.execute('''   DELETE 
                    FROM ingestedtoingested
                    WHERE ingestedparentuuid NOT IN (SELECT uuid FROM ingested)
                    OR ingestedchilduuid NOT IN (SELECT uuid FROM ingested);''')
    ingestedToIngestedRowsDeleted = c.rowcount
    print 'deleted {} rows from ingestedtoingested (unreferenced)'.format(ingestedToIngestedRowsDeleted)

    connection.commit()
    return ingestedRowsDeleted + ingestedToIngestedRowsDeleted

def deleteUnnecessaryRows(connection):
    totalDeleted = 0
    totalDeleted += deleteDeleted(conn)
    totalDeleted += deleteDuplicates(conn)

    while True:
        deletedThisPass = deleteUnreferenced(connection)
        totalDeleted += deletedThisPass
        if(deletedThisPass == 0):
            break
    
    return totalDeleted

conn = sqlite3.connect('mySymptoms_scrubbed.sqlite')
totalRowsDeleted = deleteUnnecessaryRows(conn)
print 'TOTAL ROWS DELETED: {}'.format(totalRowsDeleted)
conn.close()
```

Here I've just used the sql snippets we already built up on the first page, and run the reference pruning in a loop until no rows are deleted (random discovery: python has no `do...while` loop >:().

Running it using a hastily concocted make file, the output looks about right:

```console
$ make
rm mySymptoms_scrubbed.sqlite
cp mySymptoms.sqlite mySymptoms_scrubbed.sqlite
python scrub.py
deleted 64 rows from ingested (marked as deleted)
deleted 4 rows from reactionevent (marked as deleted)
deleted 1376 rows from ingested (duplicates)
deleted 257 rows from ingestedtoingested (duplicates)
deleted 1225 rows from ingested (unreferenced)
deleted 150 rows from ingestedtoingested (unreferenced)
deleted 55 rows from ingested (unreferenced)
deleted 3 rows from ingestedtoingested (unreferenced)
deleted 5 rows from ingested (unreferenced)
deleted 0 rows from ingestedtoingested (unreferenced)
deleted 1 rows from ingested (unreferenced)
deleted 0 rows from ingestedtoingested (unreferenced)
deleted 0 rows from ingested (unreferenced)
deleted 0 rows from ingestedtoingested (unreferenced)
TOTAL ROWS DELETED: 3140
```