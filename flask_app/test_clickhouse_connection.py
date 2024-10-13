from clickhouse_driver import Client

client = Client(host='localhost', port=9000)

try:
    result = client.execute('SELECT 1')
    print(f"Connected successfully. Result: {result}")
except Exception as e:
    print(f"Connection failed: {e}")