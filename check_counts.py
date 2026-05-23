import sqlite3
tables_to_check = ['accounts_book', 'accounts_author', 'accounts_genre', 'auth_user']
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
for table in tables_to_check:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table};")
        count = cursor.fetchone()[0]
        print(f"{table}: {count}")
    except Exception as e:
        print(f"Error checking {table}: {e}")
