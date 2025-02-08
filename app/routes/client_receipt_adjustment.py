
from flask import Blueprint, jsonify
from app.db import get_db_connection

cra_bp = Blueprint("cra", __name__)

@cra_bp.route('/cra', methods=['GET'])
def cra():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
            SELECT crm.CLIENT_ID, 
                   BILLING.PKG_BILLING.GET_CLIENT_NAME(crm.CLIENT_ID) AS CLIENT_NAME,
                   HIS.PKG_PATIENT.GET_PATIENT_NAME(d2.MRNO) AS PATIENT_NAME,
                   d2.MRNO,
                   d2.invoice_amount AS BILL_AMOUNT,
                   NVL(d2.received_amount, 0) AS RECEIVED_AMOUNT,
                   d2.invoice_amount - NVL(d2.received_amount, 0) AS REMAINING_AMOUNT,
                   d2.adjusted_amount,
                   d2.adjust_amount,
                   d2.CLIENT_INVOICE_NO,
                   d2.final_receipt_no,
                   crm.receive_no,
                   crm.total_amount AS cash_receive_amount,
                   crm.receive_date
            FROM BILLING.FRANCHISE_CHEQUE FC
            JOIN BILLING.FINAL_RECEIPT_DETAIL2 D2 ON d2.final_receipt_no = fc.final_receipt_no
            JOIN BILLING.CASH_RECEIVE_MASTER crm ON fc.receive_no = crm.receive_no
            WHERE d2.chk_option = 'Y'
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
