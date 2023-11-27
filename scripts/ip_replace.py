#script to update ../instance/ourteam.db

import sqlite3

conn = sqlite3.connect('instance/ourteam.db')
cursor = conn.cursor()

query = '''
UPDATE employee
SET picture_url = REPLACE(picture_url, '172.27.88.208', '172.20.14.166')
WHERE picture_url LIKE '%172.27.88.208%';
'''

cursor.execute(query)

#check if the query was successful
if cursor.rowcount == 0:
    print('No rows were updated.')
else:
    print('Updated', cursor.rowcount, 'rows.')

conn.commit()

conn.close()

