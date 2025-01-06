import sqlite3
import pandas as pd

def explore_database():
    conn = sqlite3.connect('app_collected_data.db')
    
    # Get table info
    print("\nUsers:")
    print(pd.read_sql_query("SELECT * FROM users", conn))
    
    print("\nPosts:")
    print(pd.read_sql_query("SELECT * FROM posts", conn))
    
    print("\nComments:")
    print(pd.read_sql_query("SELECT * FROM comments", conn))
    
    conn.close()

if __name__ == "__main__":
    explore_database() 