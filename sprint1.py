from flask import Flask, jsonify, request
import creds
from mysql.connector import Error
import mysql.connector


app = Flask(__name__)


#Builds connection to SQL database
def create_connection(host_name, user_name, user_password, db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host=host_name,
            user=user_name,
            passwd=user_password,
            database=db_name
        )
        print("Connection to MySQL DB successful")
    except Error as e:
        print(f"The error '{e}' occurred")


    return connection


#Uses Creds.py to build easier connection so don't have to type out def create conn every time
myCreds = creds.Creds()
connection = create_connection(myCreds.conString, myCreds.userName, myCreds.password, myCreds.dbName)


LEVELS = ['Bronze', 'Silver', 'Gold']
LEVEL_RANK = {'Bronze': 1, 'Silver': 2, 'Gold': 3}

#Helper Section

def error(msg, code=400):
    return jsonify({'error': msg}), code

#Showcase members endpoint for testing connection
@app.route('/members', methods=['GET'])
def get_members():
    """Return all members."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM member")
    members = cur.fetchall()
    cur.close()
    return jsonify(members), 200



#Showcases getting a single member by ID and error handling for not found
@app.route('/members/<int:member_id>', methods=['GET'])
def get_member(member_id):
    """Return a single member by ID."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM member WHERE id = %s", (member_id,))
    member = cur.fetchone()
    cur.close()
    if not member:
        return error('Member not found', 404)
    return jsonify(member), 200



#Showcases creating a member with validation and error handling for bad input
@app.route('/members', methods=['POST'])
def create_member():
    """Create a new member.


    Body (JSON):
        name     (str, required)
        details  (str, optional)
        title    (str, optional)
        level    (str, required) – Bronze | Silver | Gold
    """
    data = request.get_json()
    if not data:
        return error('Request body must be JSON')


    name  = data.get('name', '').strip()
    level = data.get('level', '').strip()


    if not name:
        return error('name is required')
    if level not in LEVELS:
        return error(f'level must be one of {LEVELS}')


    details = data.get('details', '')
    title   = data.get('title', '')


    cur = mysql.connection.cursor()
    cur.execute(
        "INSERT INTO member (name, details, title, level) VALUES (%s, %s, %s, %s)",
        (name, details, title, level)
    )
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return jsonify({'message': 'Member created', 'id': new_id}), 201

#Showcases updating an existing member with full or partial update 
@app.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """Update an existing member (full or partial update)."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM member WHERE id = %s", (member_id,))
    member = cur.fetchone()
    if not member:
        cur.close()
        return error('Member not found', 404)


    data = request.get_json()
    if not data:
        cur.close()
        return error('Request body must be JSON')


    name    = data.get('name',    member['name']).strip()
    details = data.get('details', member['details'])
    title   = data.get('title',   member['title'])
    level   = data.get('level',   member['level']).strip()


    if not name:
        cur.close()
        return error('name cannot be empty')
    if level not in LEVELS:
        cur.close()
        return error(f'level must be one of {LEVELS}')


    cur.execute(
        "UPDATE member SET name=%s, details=%s, title=%s, level=%s WHERE id=%s",
        (name, details, title, level, member_id)
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Member updated'}), 200


#Showcases deleting a member with error handling for not found and cascading delete of registrations
@app.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    """Delete a member (cascades to registrations)."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM member WHERE id = %s", (member_id,))
    if not cur.fetchone():
        cur.close()
        return error('Member not found', 404)


    cur.execute("DELETE FROM member WHERE id = %s", (member_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Member deleted'}), 200

#EVENT ENDPOINTS SECTION 

#Showcases getting all events
@app.route('/events', methods=['GET'])
def get_events():
    """Return all events."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM event")
    events = cur.fetchall()
    cur.close()
    return jsonify(events), 200



#Showcases returning a single event by ID with error handling for not found
@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Return a single event by ID."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM event WHERE id = %s", (event_id,))
    event = cur.fetchone()
    cur.close()
    if not event:
        return error('Event not found', 404)
    return jsonify(event), 200



#Showcases creating an event with validation and error handling for bad input and business rule of unique date
@app.route('/events', methods=['POST'])
def create_event():
    """Create a new event.


    Body (JSON):
        name      (str,  required)
        capacity  (int,  required)
        level     (str,  required) – Bronze | Silver | Gold
        date      (str,  required) – YYYY-MM-DD
    """
    data = request.get_json()
    if not data:
        return error('Request body must be JSON')


    name     = data.get('name', '').strip()
    capacity = data.get('capacity')
    level    = data.get('level', '').strip()
    date     = data.get('date', '').strip()


    if not name:
        return error('name is required')
    if capacity is None or not str(capacity).isdigit() or int(capacity) <= 0:
        return error('capacity must be a positive integer')
    if level not in LEVELS:
        return error(f'level must be one of {LEVELS}')
    if not date:
        return error('date is required (YYYY-MM-DD)')


    cur = mysql.connection.cursor()


    # Business rule: no two events on the same date 
    cur.execute("SELECT id FROM event WHERE date = %s", (date,))
    if cur.fetchone():
        cur.close()
        return error('An event already exists on this date'), 409


    cur.execute(
        "INSERT INTO event (name, capacity, level, date) VALUES (%s, %s, %s, %s)",
        (name, int(capacity), level, date)
    )
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return jsonify({'message': 'Event created', 'id': new_id}), 201



#Showcases updating an existing event with full or partial update, validation, and business rule of unique date (excluding self)
@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an existing event (full or partial update)."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM event WHERE id = %s", (event_id,))
    event = cur.fetchone()
    if not event:
        cur.close()
        return error('Event not found', 404)


    data = request.get_json()
    if not data:
        cur.close()
        return error('Request body must be JSON')


    name     = data.get('name',     event['name']).strip()
    capacity = data.get('capacity', event['capacity'])
    level    = data.get('level',    event['level']).strip()
    date     = data.get('date',     str(event['date'])).strip()


    if not name:
        cur.close()
        return error('name cannot be empty')
    if not str(capacity).isdigit() or int(capacity) <= 0:
        cur.close()
        return error('capacity must be a positive integer')
    if level not in LEVELS:
        cur.close()
        return error(f'level must be one of {LEVELS}')


    # Business rule: unique date (exclude current event)
    cur.execute("SELECT id FROM event WHERE date = %s AND id != %s", (date, event_id))
    if cur.fetchone():
        cur.close()
        return error('Another event already exists on this date'), 409


    cur.execute(
        "UPDATE event SET name=%s, capacity=%s, level=%s, date=%s WHERE id=%s",
        (name, int(capacity), level, date, event_id)
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Event updated'}), 200



#Showcases deleting an event with error handling for not found and cascading delete of registrations
@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event (cascades to registrations)."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM event WHERE id = %s", (event_id,))
    if not cur.fetchone():
        cur.close()
        return error('Event not found', 404)


    cur.execute("DELETE FROM event WHERE id = %s", (event_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Event deleted'}), 200