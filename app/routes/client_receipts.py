from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

cr_bp = Blueprint("cr", __name__)
CORS(cr_bp, resources={
    r"/cr": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@cr_bp.route('/cr', methods=['POST', 'OPTIONS'])
def cr():
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
        --------Client_Receipts---------
select crm.receive_date, crm.received_by, i.NAME received_by_name, crm.receive_no,pm.description payment_mode,  crd.instrument_no,
       crd.amount net_amount, crd.wht_tax, crd.amount+nvl(crd.wht_tax,0) Gross_amount,
       crm.client_id, c.name client, crd.final_invoice_no, crm.remarks
from billing.cash_receive_master crm, billing.cash_receive_detail crd, billing.client c,
     hrd.vu_information i, billing.payment_mode pm
where crm.receive_no = crd.receive_no
and   crm.client_id  = c.client_id
and   crm.received_by = i.MRNO
and   crm.receive_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
and   crm.receive_date  < TO_DATE(:end_date, 'YYYY-MM-DD')
and   crd.payment_mode_id = pm.payment_mode_id
and crm.receive_no not in (select crm.receipt_no from billing.cash_refund_master crm where crm.client_id is not null)
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
                if columns[col].upper() == 'RECEIVE_DATE':
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
            download_name=f'client_receipts_{start_date}_to_{end_date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500