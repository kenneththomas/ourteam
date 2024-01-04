import sqlite3
import os
import sys

sql = '''
ALTER TABLE employee ADD COLUMN bio TEXT;
ALTER TABLE employee ADD COLUMN location TEXT;
'''

#check if db exists
if not os.path.exists('../instance/ourteam.db'):
    print('ourteam.db not found')
    sys.exit(1)

#connect to db
conn = sqlite3.connect('../instance/ourteam.db')
c = conn.cursor()

#execute sql
c.executescript(sql)

#commit and close
conn.commit()

conn.close()

print('Done')