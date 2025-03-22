from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

don_bp = Blueprint("don", __name__)
CORS(don_bp, resources={
    r"/don": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@don_bp.route('/don', methods=['POST', 'OPTIONS'])
def don():
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight request successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200

    # Handle POST request
    data = request.get_json()
    receipts_no = data.get('receipts_no')



    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = '''
select don.receipt_no, don.receipt_location_id, don.trans_date receipt_date, don.coa_code_cr,
       NVL(don.name_for_other, don.donor_name) party_name,
       NVL(don.address_for_other, don.donor_address) address,
       NVL(c.coa_description,
           (select dt.description
            from marketing.donation_types dt
            where dt.donation_type_id = don.donation_type_id
            and dt.donation_group_id = don.donation_group_id)) On_Account_of,
       pm.description mode_of_payment, don.cheque_no,  don.amount,
       --       to_char(to_date(don.amount, 'J'), 'JSP') || ' ONLY' Amount_in_Words,
       don.remarks, don.received_by Cashier,
       sysdate         printed_on,    r.mobile
from marketing.donation       don,
       marketing.donor          r,
       marketing.donation_types dt,
       billing.payment_mode     pm,
       finance.gl_coa           c
where don.donor_id = r.donor_id
       and don.donation_type_id = dt.donation_type_id
       and don.donation_group_id = dt.donation_group_id
       and don.mode_id = pm.payment_mode_id
       and don.coa_code_cr = c.coa_code(+)
       and don.receipt_location_id='101'
       and don.receipt_no=:receipts_no 

        '''

        cursor.execute(query, {
            'receipts_no': receipts_no,


        })


        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        result = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500