from flask import Flask, render_template, request, g
from clickhouse_driver import Client
import os

app = Flask(__name__)

# Use localhost since we're connecting from the host machine
clickhouse_host = 'localhost'
clickhouse_port = 9000  # Use 9000 for native protocol

def get_clickhouse_client():
    if 'clickhouse_client' not in g:
        g.clickhouse_client = Client(host=clickhouse_host, port=clickhouse_port)
    return g.clickhouse_client

@app.teardown_appcontext
def close_clickhouse_client(error):
    client = g.pop('clickhouse_client', None)
    if client is not None:
        client.disconnect()

@app.route('/', methods=['GET', 'POST'])
def index():
    # Get filter parameters from the request
    log_level = request.args.get('log_level', '')
    source = request.args.get('source', '')
    message = request.args.get('message', '')

    # Build the query dynamically based on filter
    base_query = """
        SELECT timestamp, log_level, message, source
        FROM logs.application_logs
    """

    conditions = []
    query_params = {}

    if log_level:
        conditions.append("log_level = %(log_level)s")
        query_params['log_level'] = log_level

    if source:
        conditions.append("source = %(source)s")
        query_params['source'] = source

    if message:
        conditions.append("message LIKE %(message)s")
        query_params['message'] = f"%{message}%"

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY timestamp DESC LIMIT 100"

    # Execute the query
    client = get_clickhouse_client()
    result = client.execute(base_query, query_params)
    logs = [dict(zip(['timestamp', 'log_level', 'message', 'source'], row)) for row in result]

    return render_template('index.html', logs=logs, log_level=log_level, source=source, message=message)

if __name__ == '__main__':
    app.run(debug=True)