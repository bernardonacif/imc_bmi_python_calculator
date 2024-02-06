import sqlite3

def erase_db(table):
    try:
        conn = sqlite3.connect('./SQLite/imc_bmi.db')
        cursor = conn.cursor()
        cursor.execute(f'DELETE FROM {table}')
        conn.commit()
        print(f'Table {table} successfully truncated.')
    except sqlite3.Error as e:
        print(f'Error truncating table: {e}')
    finally:
        conn.close()


erase_db('user')  
erase_db('user_reports')  
