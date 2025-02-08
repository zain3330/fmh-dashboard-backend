from flask import Blueprint, jsonify, request
from flask_cors import CORS
from app.db import get_db_connection

gl_bp = Blueprint("gl", __name__)
CORS(gl_bp, resources={
    r"/gl": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@gl_bp.route('/gl', methods=['POST', 'OPTIONS'])
def gl():
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight request successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200

    # Handle POST request
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    coa_short = data.get('coa_short')
    coa_code_start = data.get('coa_code_start')
    coa_code_end = data.get('coa_code_end')

    # Validate required fields
    if not all([start_date, end_date, coa_short, coa_code_start, coa_code_end]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = '''
        SELECT gtm.voucher_type, 
               gtm.voucher_no, 
               gtm.trans_date, 
               gtm.reference_no AS CHEQUE_NO, 
               gtm.remarks AS VOUCHER_REMARKS, 
               gtd.coa_code, 
               gc.coa_description, 
               gtd.ledger_type_code, 
               gtd.sub_ldgr_item_code, 
               gsl.sub_ldgr_item_desc, 
               gtd.narration, 
               gtd.dr_amount, 
               gtd.cr_amount
        FROM   finance.gl_tran_detail gtd
               INNER JOIN finance.gl_tran_master gtm 
                       ON gtd.voucher_type = gtm.voucher_type 
                      AND gtd.voucher_no = gtm.voucher_no
               INNER JOIN finance.gl_coa gc 
                       ON gtd.coa_code = gc.coa_code
               LEFT JOIN finance.gl_sub_ledgers gsl 
                      ON gtd.ledger_type_code = gsl.ledger_type_code
                     AND gtd.sub_ldgr_item_code = gsl.sub_ldgr_item_code
        WHERE  gtm.trans_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
               AND gtm.trans_date < TO_DATE(:end_date, 'YYYY-MM-DD')
               AND gtd.coa_code LIKE :coa_short
               AND gtm.voucher_status IN ('P', 'T')
               AND gtd.coa_code BETWEEN :coa_code_start AND :coa_code_end
        ORDER  BY gtm.trans_date, gtm.voucher_type, gtm.voucher_no
        '''

        cursor.execute(query, {
            'start_date': start_date,
            'end_date': end_date,
            'coa_short': f'{coa_short}%',
            'coa_code_start': coa_code_start,
            'coa_code_end': coa_code_end
        })

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        result = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
