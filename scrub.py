import sqlite3

def deleteDeleted(connection):
    c = connection.cursor()

    c.execute('''   DELETE
                    FROM ingested
                    WHERE deleted != 0;''')
    ingestedRowsDeleted = c.rowcount
    print 'deleted {} ingested rows marked as deleted'.format(ingestedRowsDeleted)

    c.execute('''   DELETE
                    FROM reactionevent
                    WHERE deleted != 0;''')
    reactionEventRowsDeleted = c.rowcount
    print 'deleted {} reactionevent rows marked as deleted'.format(reactionEventRowsDeleted)

    connection.commit()
    return ingestedRowsDeleted + reactionEventRowsDeleted

conn = sqlite3.connect('mySymptoms_scrubbed.sqlite')
deleteDeleted(conn)
conn.close()