from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

pftb_bp = Blueprint("pftb", __name__)
CORS(pftb_bp, resources={
    r"/pftb": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@pftb_bp.route('/pftb', methods=['POST', 'OPTIONS'])
def pftb():
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight request successful"})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        return response, 200

    # Handle POST request
    data = request.get_json()
    year = data.get('year')



    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = ''' 
Select o.coa_code, c.coa_description, o.sub_ldgr_item_code, sl.sub_ldgr_item_desc, SUM(o.open_dr) open_dr, SUM(o.open_cr) open_cr,
       SUM(o.tran_dr) tran_dr, SUM(o.tran_cr) tran_cr, SUM(o.open_dr-o.open_cr+o.tran_dr-o.tran_cr) Closing
From Finance.Gl_Opening_Balances o, Finance.Gl_Sub_Ledgers sl, finance.gl_coa c
Where o.year_code = :year ------2023-24
and  o.coa_code like '8%'
and  c.coa_code = o.coa_code
and  sl.ledger_type_code = o.ledger_type_code
and  sl.sub_ldgr_item_code = o.sub_ldgr_item_code
group by o.coa_code, o.sub_ldgr_item_code, sl.sub_ldgr_item_desc, c.coa_description
order by 1,2
        '''

        cursor.execute(query, {
            'year': year,

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
                if columns[col].upper() in ['TRANS_DATE']:
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
            download_name=f'monthly_stock_report_{year}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500