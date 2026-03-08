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