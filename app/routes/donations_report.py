from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

dr_bp = Blueprint("dr", __name__)
CORS(dr_bp, resources={
    r"/dr": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@dr_bp.route('/dr', methods=['POST', 'OPTIONS'])
def dr():
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
       and don.trans_date between TO_DATE(:start_date, 'YYYY-MM-DD')
       and TO_DATE(:end_date, 'YYYY-MM-DD')

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
                if columns[col].upper() in ['RECEIPT_DATE', 'PRINTED_ON']:
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
            download_name=f'donation_report_{start_date}_to_{end_date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500