import sqlite3
import os


def add_missing_columns():
    # Path to your database
    db_path = 'instance/hope_foundation.db'

    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        print("Make sure your Flask app has run at least once")
        return

    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get existing columns in donations table
    cursor.execute("PRAGMA table_info(donations)")
    existing_columns = [column[1] for column in cursor.fetchall()]

    print("=" * 50)
    print("Current columns in donations table:")
    print(existing_columns)
    print("=" * 50)

    # Define columns to add
    columns_to_add = [
        ('checkout_request_id', 'VARCHAR(100)'),
        ('receipt_number', 'VARCHAR(50)'),
        ('completed_at', 'TIMESTAMP')
    ]

    # Add missing columns
    added_count = 0
    for column_name, column_type in columns_to_add:
        if column_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE donations ADD COLUMN {column_name} {column_type}")
                print(f"✅ Added column: {column_name}")
                added_count += 1
            except Exception as e:
                print(f"❌ Error adding {column_name}: {str(e)}")
        else:
            print(f"⏭️ Column already exists: {column_name}")

    # Commit changes
    conn.commit()

    # Verify columns after addition
    cursor.execute("PRAGMA table_info(donations)")
    updated_columns = [column[1] for column in cursor.fetchall()]

    print("=" * 50)
    print("Updated columns in donations table:")
    print(updated_columns)
    print("=" * 50)

    if added_count > 0:
        print(f"✅ Successfully added {added_count} new column(s)!")
    else:
        print("✅ All columns already exist!")

    conn.close()


if __name__ == '__main__':
    add_missing_columns()
