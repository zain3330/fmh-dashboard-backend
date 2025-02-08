from flask import Blueprint, jsonify
from app.db import get_db_connection

codes_bp = Blueprint("codes", __name__)

@codes_bp.route('/codes', methods=['GET'])  # Add @codes_bp.route decorator
def codes():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
        SELECT DISTINCT gc.coa_code, gc.coa_description
        FROM finance.gl_coa gc
        JOIN FINANCE.GL_SUB_LEDGERS GSL ON gc.ledger_type_code = gsl.ledger_type_code
        WHERE gc.coa_level_code = '4'
        ORDER BY gc.coa_code
        '''

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        result = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
