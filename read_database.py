import sqlite3

def read_database():
    conn = sqlite3.connect('/home/vittorusso/data.db')  # SQLite database file
    cursor = conn.cursor()

    # Query to fetch all data from the table
    cursor.execute('SELECT * FROM scraped_data')
    rows = cursor.fetchall()

    # Print the data
    for row in rows:
        print(row)

    conn.close()

if __name__ == "__main__":
    read_database()