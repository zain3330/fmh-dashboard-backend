from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

ccr_bp = Blueprint("ccr", __name__)
CORS(ccr_bp, resources={
    r"/ccr": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@ccr_bp.route('/ccr', methods=['POST', 'OPTIONS'])
def ccr():
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

    # Validate required fields
    if not all([start_date, end_date]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = '''
      select crm.receive_date, crm.sale_id, crm.invoice_no, crd.receive_no, crd.amount, pm.description, crd.instrument_no, crd.validity_date
from billing.cash_receive_master crm, billing.cash_receive_detail crd, billing.payment_mode_wise_merchant pm
where crm.receive_no = crd.receive_no
and   crd.merchant_id = pm.merchant_id
and   crm.receive_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
and   crm.receive_date  < TO_DATE(:end_date, 'YYYY-MM-DD')
and   crd.payment_mode_id = '001006'
order by crm.receive_date

        '''

        cursor.execute(query, {
            'start_date': start_date,
            'end_date': end_date,

        })

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]

        # Create an in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Create date format (dd-mon-yyyy)
        date_format = workbook.add_format({
            'num_format': 'dd-mmm-yyyy'
        })

        # Write headers without formatting
        for col, header in enumerate(columns):
            worksheet.write(0, col, header)

        # Write data with date formatting only
        for row, data in enumerate(cursor, start=1):
            for col, value in enumerate(data):
                if columns[col].upper() in ['RECEIVE_DATE', 'VALIDITY_DATE']:
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
            download_name=f'credit_card_receipts_{start_date}_to_{end_date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500