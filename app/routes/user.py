from flask import Blueprint, jsonify, request
from flask_cors import CORS
from app.db import get_db_connection


user_bp = Blueprint("user", __name__)
CORS(user_bp, resources={
    r"/user": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
@user_bp.route('/user', methods=['POST'])
def get_user_count():
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response = jsonify({"message": "CORS preflight request successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200
    data = request.get_json()
    mrno = data.get('mrno')
    pin = data.get('pin')

    # Validate input
    if not mrno or not pin:
        return jsonify({"error": "Missing required fields (mrno, pin)"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = '''
        SELECT full_name, COUNT(*) AS UserCount 
        FROM security.users 
        WHERE mrno = :mrno AND pin_code = :pin
        GROUP BY full_name
        '''

        cursor.execute(query, {'mrno': mrno, 'pin': pin})
        rows = cursor.fetchall()

        result = [{"full_name": row[0], "UserCount": row[1]} for row in rows]

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
