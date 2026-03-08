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

#  REGISTRATION ENDPOINTS SECTION

#Showcases getting all registrations with joined member and event names for easier frontend display
@app.route('/registrations', methods=['GET'])
def get_registrations():
    """Return all registrations (with joined member & event names)."""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.id, r.event_id, r.member_id,
               e.name AS event_name, m.name AS member_name
        FROM registration r
        JOIN event  e ON r.event_id  = e.id
        JOIN member m ON r.member_id = m.id
    """)
    registrations = cur.fetchall()
    cur.close()
    return jsonify(registrations), 200



#Showcases returning a single registration by ID with joined member and event names and error handling for not found
@app.route('/registrations/<int:reg_id>', methods=['GET'])
def get_registration(reg_id):
    """Return a single registration by ID."""
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT r.id, r.event_id, r.member_id,
               e.name AS event_name, m.name AS member_name
        FROM registration r
        JOIN event  e ON r.event_id  = e.id
        JOIN member m ON r.member_id = m.id
        WHERE r.id = %s
    """, (reg_id,))
    reg = cur.fetchone()
    cur.close()
    if not reg:
        return error('Registration not found', 404)
    return jsonify(reg), 200



#Showcases returning all members registered for a specific event with error handling for event not found
@app.route('/events/<int:event_id>/members', methods=['GET'])
def get_members_for_event(event_id):
    """Return all members registered for a specific event."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM event WHERE id = %s", (event_id,))
    if not cur.fetchone():
        cur.close()
        return error('Event not found', 404)


    cur.execute("""
        SELECT m.id, m.name, m.title, m.level
        FROM member m
        JOIN registration r ON r.member_id = m.id
        WHERE r.event_id = %s
    """, (event_id,))
    members = cur.fetchall()
    cur.close()
    return jsonify(members), 200



#Showcases registering a member to an event with validation and error handling for bad input and business rules
#Shows business rules of member level must be >= event level, event must not be at capacity, and member cannot register for same event twice
@app.route('/registrations', methods=['POST'])
def create_registration():
    """Register a member to an event.


    Body (JSON):
        event_id   (int, required)
        member_id  (int, required)


    Business rules enforced:
        1. Member level must be >= event level.
        2. Event must not be at capacity.
        3. Member cannot register for the same event twice.
    """
    data = request.get_json()
    if not data:
        return error('Request body must be JSON')


    event_id  = data.get('event_id')
    member_id = data.get('member_id')


    if event_id is None or member_id is None:
        return error('event_id and member_id are required')


    cur = mysql.connection.cursor()


    # Fetch event
    cur.execute("SELECT * FROM event WHERE id = %s", (event_id,))
    event = cur.fetchone()
    if not event:
        cur.close()
        return error('Event not found', 404)


    # Fetch member
    cur.execute("SELECT * FROM member WHERE id = %s", (member_id,))
    member = cur.fetchone()
    if not member:
        cur.close()
        return error('Member not found', 404)


    # Business rule 1: level check
    if LEVEL_RANK[member['level']] < LEVEL_RANK[event['level']]:
        cur.close()
        return error(
            f"Member level '{member['level']}' is insufficient for a "
            f"'{event['level']}' event"
        ), 403


    # Business rule 2: capacity check
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM registration WHERE event_id = %s",
        (event_id,)
    )
    count = cur.fetchone()['cnt']
    if count >= event['capacity']:
        cur.close()
        return error('Event is at full capacity'), 409


    # Business rule 3: duplicate registration
    cur.execute(
        "SELECT id FROM registration WHERE event_id = %s AND member_id = %s",
        (event_id, member_id)
    )
    if cur.fetchone():
        cur.close()
        return error('Member is already registered for this event'), 409


    cur.execute(
        "INSERT INTO registration (event_id, member_id) VALUES (%s, %s)",
        (event_id, member_id)
    )
    mysql.connection.commit()
    new_id = cur.lastrowid
    cur.close()
    return jsonify({'message': 'Registration created', 'id': new_id}), 201



#Showcases updating a registration to change the event and/or member with validation and error handling for bad input and business rules
@app.route('/registrations/<int:reg_id>', methods=['PUT'])
def update_registration(reg_id):
    """Update a registration (change event and/or member).


    Body (JSON):
        event_id   (int, optional)
        member_id  (int, optional)


    The same business rules as POST apply.
    """
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM registration WHERE id = %s", (reg_id,))
    reg = cur.fetchone()
    if not reg:
        cur.close()
        return error('Registration not found', 404)


    data = request.get_json()
    if not data:
        cur.close()
        return error('Request body must be JSON')


    new_event_id  = data.get('event_id',  reg['event_id'])
    new_member_id = data.get('member_id', reg['member_id'])


    # Fetch event
    cur.execute("SELECT * FROM event WHERE id = %s", (new_event_id,))
    event = cur.fetchone()
    if not event:
        cur.close()
        return error('Event not found', 404)


    # Fetch member
    cur.execute("SELECT * FROM member WHERE id = %s", (new_member_id,))
    member = cur.fetchone()
    if not member:
        cur.close()
        return error('Member not found', 404)


    # Level check
    if LEVEL_RANK[member['level']] < LEVEL_RANK[event['level']]:
        cur.close()
        return error(
            f"Member level '{member['level']}' is insufficient for a "
            f"'{event['level']}' event"
        ), 403


    # Capacity check (exclude current registration's event if same)
    cur.execute(
        "SELECT COUNT(*) AS cnt FROM registration WHERE event_id = %s AND id != %s",
        (new_event_id, reg_id)
    )
    count = cur.fetchone()['cnt']
    if count >= event['capacity']:
        cur.close()
        return error('Event is at full capacity'), 409


    # Duplicate check (exclude self)
    cur.execute(
        "SELECT id FROM registration WHERE event_id=%s AND member_id=%s AND id != %s",
        (new_event_id, new_member_id, reg_id)
    )
    if cur.fetchone():
        cur.close()
        return error('Member is already registered for this event'), 409


    cur.execute(
        "UPDATE registration SET event_id=%s, member_id=%s WHERE id=%s",
        (new_event_id, new_member_id, reg_id)
    )
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Registration updated'}), 200



#Showcases deleting a registration with error handling for not found
@app.route('/registrations/<int:reg_id>', methods=['DELETE'])
def delete_registration(reg_id):
    """Delete a registration."""
    cur = mysql.connection.cursor()
    cur.execute("SELECT id FROM registration WHERE id = %s", (reg_id,))
    if not cur.fetchone():
        cur.close()
        return error('Registration not found', 404)


    cur.execute("DELETE FROM registration WHERE id = %s", (reg_id,))
    mysql.connection.commit()
    cur.close()
    return jsonify({'message': 'Registration deleted'}), 200