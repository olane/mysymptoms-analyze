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