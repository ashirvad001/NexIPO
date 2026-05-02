import sqlite3
conn = sqlite3.connect('ipo_intelligence.db')
cursor = conn.cursor()
cursor.execute("SELECT id, company_name FROM ipos WHERE company_name LIKE '%kissht%'")
print(cursor.fetchall())
