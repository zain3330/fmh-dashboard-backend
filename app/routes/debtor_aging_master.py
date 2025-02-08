
from flask import Blueprint, jsonify
from app.db import get_db_connection

dam_bp = Blueprint("dam", __name__)

@dam_bp.route('/dam', methods=['GET'])
def dam():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
          SELECT FM.CLIENT_ID, CL.NAME, FM.PROCESS_ID, FM.FINAL_INVOICE_DATE, FM.CLIENT_INVOICE_NO,

       (SELECT MIN(LM.CLIENT_REF_NO)
       FROM FINANCE.PBS_TRAN_DETAIL_CORPORATE PTDC, BILLING.REF_LETTER_MASTER LM
       WHERE PTDC.REF_LETTER_NO IS NOT NULL
       AND PTDC.PROCESS_ID = FM.PROCESS_ID
       AND PTDC.CLIENT_ID = FM.CLIENT_ID
       AND PTDC.FINAL_INVOICE_NO = FM.CLIENT_INVOICE_NO
       AND PTDC.MRNO = P.MRNO
       AND PTDC.REF_LETTER_NO = LM.REF_LETTER_NO) REF_LETTER_NO,

       FM.MRNO, P.NIC_NEW,

      (SELECT MAX(PTDC.ADMISSION_NO)
      FROM FINANCE.PBS_TRAN_DETAIL_CORPORATE PTDC
      WHERE PTDC.PROCESS_ID = FM.PROCESS_ID
      AND PTDC.CLIENT_ID = FM.CLIENT_ID
      AND PTDC.FINAL_INVOICE_NO = FM.CLIENT_INVOICE_NO
      AND PTDC.MRNO = P.MRNO) ADMISSION_NO,

      (SELECT MAX(FIM.ADMISSION_DATE)
      FROM FINANCE.PBS_TRAN_DETAIL_CORPORATE PTDC, BILLING.FINAL_INVOICE_MASTER FIM
      WHERE PTDC.PROCESS_ID = FM.PROCESS_ID
      AND PTDC.CLIENT_ID = FM.CLIENT_ID
      AND PTDC.FINAL_INVOICE_NO = FM.CLIENT_INVOICE_NO
      AND PTDC.MRNO = P.MRNO
      AND PTDC.ADMISSION_NO = FIM.ADMISSION_NO
      AND PTDC.MRNO = FIM.MRNO) ADMISSION_DATE,

      P.NAME, FM.NET_RECEIVABLE, FM.RECEIVED_AMOUNT, (NVL(FM.NET_RECEIVABLE, 0) - NVL(FM.RECEIVED_AMOUNT, 0)) REMAINING,
      FM.FINAL_INVOICE_TYPE, FM.CLIENT_INVOICE_NO, FM.FINAL_INVOICE_NO

      FROM BILLING.FINAL_INVOICE_MASTER FM, BILLING.CLIENT CL, REGISTRATION.V_PATIENT P
      WHERE FM.CLIENT_ID = CL.CLIENT_ID
      AND FM.MRNO = P.MRNO
      AND FM.CLIENT_ID IS NOT NULL
      AND NVL(ABS(FM.NET_RECEIVABLE), 0) - NVL(FM.RECEIVED_AMOUNT, 0) > 0
      AND FM.MRNO IS NOT NULL
      AND FM.CLIENT_INVOICE_NO IN

      (SELECT FIM.FINAL_INVOICE_NO
      FROM BILLING.FINAL_INVOICE_MASTER FIM
      WHERE NVL(FIM.NET_RECEIVABLE, 0) > NVL(FIM.RECEIVED_AMOUNT, 0)
      AND FIM.FINAL_INVOICE_TYPE IN ('R', 'H')
      AND FIM.FINAL_INVOICE_DATE > '01-JAN-2016')
      AND FM.FINAL_INVOICE_TYPE IN ('I', 'O', 'H')

ORDER BY 1, 4
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
