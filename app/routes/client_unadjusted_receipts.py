from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

cur_bp = Blueprint("cur", __name__)
CORS(cur_bp, resources={
    r"/cur": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@cur_bp.route('/cur', methods=['GET', 'OPTIONS'])
def cur():
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
select cl.client_id, cl.name, cr.receive_date, cr.receive_no, crd.instrument_no,
       sum(nvl(crd.amount,0)+nvl(crd.wht_tax,0)-nvl(crd.received_amount,0)) Amount
from billing.cash_receive_master cr, billing.client cl, billing.cash_receive_detail crd
where cr.client_id=cl.client_id
and cr.receive_no=crd.receive_no
and cr.client_id is not null
and  Upper (cl.name) not like '%FUND%'
and  Upper (cl.name) not like '%NEPHRO%'
and  Upper (cl.name) not like '%HAMD%'
AND (nvl(crd.amount,0)+nvl(crd.wht_tax,0)-nvl(crd.received_amount,0)) > 50
and cr.receive_no not in (select crm.receipt_no from billing.cash_refund_master crm where crm.client_id is not null)
group by cl.client_id, cl.name, cr.receive_date, cr.receive_no, crd.instrument_no
Order by cr.receive_date

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
            download_name='client_unadjusted_receipts.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
