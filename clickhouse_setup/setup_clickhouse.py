from clickhouse_driver import Client
import time

def setup_database():
    # Initialize the ClickHouse client
    # Use the container name as the host
    client = Client(host='clickhouse-server', port=9000)

    max_attempts = 5
    attempt = 0

    while attempt < max_attempts:
        try:
            # Create the 'logs' database if it doesn't exist
            client.execute('CREATE DATABASE IF NOT EXISTS logs')

            # Drop the existing table if it exists
            client.execute('DROP TABLE IF EXISTS logs.application_logs')

            # Create the 'application_logs' table with the updated schema
            client.execute('''
                CREATE TABLE IF NOT EXISTS logs.application_logs (
                    timestamp DateTime,
                    log_level String,
                    message String,
                    source String
                ) ENGINE = MergeTree()
                ORDER BY timestamp
            ''')

            print("Database 'logs' and table 'application_logs' have been created successfully.")
            break
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            attempt += 1
            time.sleep(5)  # Wait for 5 seconds before retrying

    if attempt == max_attempts:
        print("Failed to set up the database after multiple attempts.")

if __name__ == "__main__":
    setup_database()