from flask import Blueprint, jsonify
from app.db import get_db_connection

ssp_bp = Blueprint("ssp", __name__)

@ssp_bp.route('/ssp', methods=['GET'])
def ssp():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
            Select td.client_id, c.name client_name, td.mrno, p.name, td.trans_no, td.admission_no, td.ref_letter_no, lm.client_ref_no, lm.trans_date ref_letter_trans_date, sum(td.dr_amount-td.cr_amount) Amount
            From finance.pbs_tran_detail td, BILLING.REF_LETTER_MASTER LM, registration.v_patient p, billing.client c
            Where td.client_id = '1012000041'
            and  td.coa_code = '911010'
            and  td.client_id = c.client_id
            and  td.REF_LETTER_NO IS NOT NULL
            and  td.REF_LETTER_NO = LM.REF_LETTER_NO
            and  lm.mrno = p.mrno
            Group by td.mrno, td.admission_no, td.ref_letter_no, lm.client_ref_no, p.name, lm.trans_date, td.trans_no, td.client_id, c.name
            order by lm.trans_date
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
