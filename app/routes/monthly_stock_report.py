from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

msr_bp = Blueprint("msr", __name__)
CORS(msr_bp, resources={
    r"/msr": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@msr_bp.route('/msr', methods=['POST', 'OPTIONS'])
def msr():
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
        SELECT 
            il.store_id, 
            s.description Store, 
            TRUNC(il.transaction_date) transaction_date, 
            il.item_id, 
            pharmacy.pkg_common.GET_DRUG_DETAIL(il.item_id) item,
            il.transaction_type_id, 
            tt.description,
            SUM(il.qty_debit) qty_debit, 
            SUM(il.qty_debit * il.moving_average_price) debt_value,
            SUM(il.qty_credit) qty_credit, 
            SUM(il.qty_credit * il.moving_average_price) credit_value,
            SUM(il.qty_debit * il.moving_average_price) - SUM(il.qty_credit * il.moving_average_price) Balance
        FROM 
            inventory.inventory_ledger il, 
            definitions.transaction_type tt, 
            item.store s
        WHERE 
            il.transaction_type_id = tt.transaction_type_id
            AND il.store_id = s.store_id
            AND s.main_sub = 'M'
            AND il.transaction_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
            AND il.transaction_date < TO_DATE(:end_date, 'YYYY-MM-DD')
        GROUP BY 
            il.store_id, 
            s.description, 
            TRUNC(il.transaction_date), 
            il.item_id, 
            pharmacy.pkg_common.GET_DRUG_DETAIL(il.item_id),
            il.transaction_type_id, 
            tt.description
        ORDER BY 
            TRUNC(il.transaction_date), 
            s.description
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
                if columns[col].upper() in ['TRANSACTION_DATE']:
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
            download_name=f'monthly_stock_report_{start_date}_to_{end_date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500