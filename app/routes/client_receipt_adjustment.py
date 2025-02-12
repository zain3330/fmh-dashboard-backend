from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

cra_bp = Blueprint("cra", __name__)
CORS(cra_bp, resources={
    r"/cra": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@cra_bp.route('/cra', methods=['GET', 'OPTIONS'])
def cra():
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight request successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response, 200

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

        # Create an in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Create date format (dd-mmm-yyyy)
        date_format = workbook.add_format({'num_format': 'dd-mmm-yyyy'})

        # Add headers
        for col, header in enumerate(columns):
            worksheet.write(0, col, header)

        # Write data
        for row, data in enumerate(cursor, start=1):
            for col, value in enumerate(data):
                if columns[col].upper() == 'RECEIVE_DATE':  # Apply date format
                    worksheet.write(row, col, value, date_format)
                else:
                    worksheet.write(row, col, value)

        workbook.close()
        output.seek(0)

        cursor.close()
        connection.close()

        return send_file(
            output,
            as_attachment=True,
            download_name='client_receipt_adjustment.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
