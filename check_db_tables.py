import sqlite3
try:
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print('Tables in db.sqlite3:')
    for t in tables:
        print(f' - {t[0]}')
    
    # Also check if accounts_book has data
    cursor.execute("SELECT COUNT(*) FROM accounts_book;")
    count = cursor.fetchone()[0]
    print(f'\nRow count in accounts_book: {count}')
except Exception as e:
    print(f'Error: {e}')
