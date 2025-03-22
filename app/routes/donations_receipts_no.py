from flask import Blueprint, jsonify
from app.db import get_db_connection

drn_bp = Blueprint("drn", __name__)

@drn_bp.route('/drn', methods=['GET'])  # Add @drn_bp.route decorator
def drn():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
  select  don.receipt_no,
        NVL(don.name_for_other, don.donor_name) party_name 
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
