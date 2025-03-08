from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

pfgl_bp = Blueprint("pfgl", __name__)
CORS(pfgl_bp, resources={
    r"/pfgl": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@pfgl_bp.route('/pfgl', methods=['POST', 'OPTIONS'])
def pfgl():
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
select gtm.voucher_type, gtm.voucher_no, gtm.trans_date, gtm.reference_no CHEQUE_NO, gtm.remarks VOUCHER_REMARKS, gtd.coa_code, gc.coa_description, gtd.ledger_type_code,  gtd.sub_ldgr_item_code, gsl.sub_ldgr_item_desc, gtd.narration, gtd.dr_amount, gtd.cr_amount
from finance.pf_tran_detail gtd, finance.pf_tran_master gtm, finance.gl_coa gc, finance.gl_sub_ledgers gsl
where gtd.voucher_type=gtm.voucher_type
and gtd.voucher_no=gtm.voucher_no
and gtd.coa_code=gc.coa_code
and gtd.ledger_type_code=gsl.ledger_type_code
and gtd.sub_ldgr_item_code=gsl.sub_ldgr_item_code
and gtm.trans_date>=TO_DATE(:start_date, 'YYYY-MM-DD')
and gtm.trans_date< TO_DATE(:end_date, 'YYYY-MM-DD')
and gtd.coa_code like '8%'
and gtm.voucher_status in ('P','T')
order by 3,1,2
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
            download_name=f'monthly_stock_report_{start_date}_to_{end_date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500