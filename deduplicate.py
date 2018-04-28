import sqlite3
import itertools

def getNamesToIds(connection):
    c = connection.cursor()
    c.execute('''   SELECT 
                        name,
                        uuid
                    FROM ingested
                ''')
    allRows = c.fetchall()

    nameFunc = lambda x: x[0]
    groupedByName = itertools.groupby(sorted(allRows, key=nameFunc), nameFunc)

    idsToNames = {key: [thing[1] for thing in group] for key, group in groupedByName}
    return idsToNames

def deduplicateItems(connection, namesToIds):
    for name, ids in namesToIds.items():
        if len(ids) > 1:
            print 'MERGING ' + str(len(ids)) + ' INSTANCES OF ' + name + ' INTO ' + ids[0]
            mergeIngested(ids[0], ids[1:], connection)

def mergeIngested(id, idsToMergeIn, connection):
    c = connection.cursor()
    c.execute('''
        
    ''')
    connection.commit()

conn = sqlite3.connect('mySymptoms_deduplicated.sqlite')

namesToIds = getNamesToIds(conn)
deduplicateItems(conn, namesToIds)

conn.close()