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

conn = sqlite3.connect('mySymptoms_deduplicated.sqlite')
namesToIds = getNamesToIds(conn)
for name, ids in namesToIds.iteritems():
    print name
    print ', '.join(ids)
conn.close()