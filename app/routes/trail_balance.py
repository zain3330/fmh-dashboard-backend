from flask import Blueprint, jsonify, request
from app.db import get_db_connection

from flask_cors import CORS

tb_bp = Blueprint("tb", __name__)
CORS(tb_bp)

@tb_bp.route('/tb', methods=['POST'])
def tb():
    data = request.get_json()
    mrno = data.get('MRNO')
    if not mrno:
        return jsonify({"error": "Missing 'MRNO' in request body"}), 400
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
        SELECT s.coa_code, s.coa_description, s.ledger_type_code, s.sub_ldgr_item_code, 
               s.sub_ledger_item_desc, s.run_open_dr, s.run_open_cr,
               s.tran_dr, s.tran_cr, s.close_dr, s.close_cr, s.user_id, s.terminal, u.mrno
        FROM finance.gl_trial_sub_ledgers s
        JOIN security.users u ON s.user_id = u.userid AND s.terminal = u.terminal
        WHERE u.mrno = :mrno
          AND (year_open_dr <> 0 OR year_open_cr <> 0 OR run_open_dr <> 0 OR
               run_open_cr <> 0 OR tran_dr <> 0 OR tran_cr <> 0)
        '''
        cursor.execute(query, {'mrno': mrno})
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        result = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
