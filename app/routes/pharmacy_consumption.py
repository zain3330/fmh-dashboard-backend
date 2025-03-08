from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

pc_bp = Blueprint("pc", __name__)
CORS(pc_bp, resources={
    r"/pc": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@pc_bp.route('/pc', methods=['POST', 'OPTIONS'])
def pc():
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
-----Pharmacy Consumption-------
select stm.trans_no, stm.approved_date, fs.description from_Store, ts.description to_Store, std.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAil(std.item_id) Drug,
       std.transfered_qty, (std.moving_average_cost * std.transfered_qty)  Value, std.cancel_qty,
       (std.moving_average_cost * std.cancel_qty)  cancel
from mms.store_transfer_master stm, item.store fs, item.store ts, hrd.vu_information i,
     mms.store_transfer_detail std
where stm.trans_no   = std.trans_no
and   stm.from_store_id = fs.store_id
and   stm.to_store_id   = ts.store_id
and   UPPER(fs.description) like '%PHARM%'
and   stm.approved_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
and   stm.approved_date < TO_DATE(:end_date, 'YYYY-MM-DD')
and   stm.delivered_by = i.MRNO
and   std.transaction_type_id = '026'
order by stm.approved_date

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
                if columns[col].upper() in ['APPROVED_DATE',]:
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
            download_name=f'pharmacy_consumption_{start_date}_to_{end_date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500