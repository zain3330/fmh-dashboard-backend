from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

ca_bp = Blueprint("ca", __name__)
CORS(ca_bp, resources={
    r"/ca": {
        "origins": "*",
        "methods": ["POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@ca_bp.route('/ca', methods=['POST', 'OPTIONS'])
def ca():
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
    coa_short = data.get('coa_short')


    # Validate required fields
    if not all([start_date, end_date, coa_short]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        query = '''
Select sl.location_id, il.move_type_id, il.store_id, st.description store, il.cost_centre_id, sl.sub_ldgr_item_desc, il.item_id, it.description item, sum(NVL(il.qty_cr,0)-NVL(il.qty_dr,0)) QTY,
       (SUM((NVL(il.qty_cr,0)-NVL(il.qty_dr,0))*(il.unit_cost))) Value
from mms.mms_item_ledger il, item.store st, item.item it, mms.def_move_type mt, FINANCE.GL_SUB_LEDGERS sl
WHERE il.trans_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
AND   il.trans_date  < TO_DATE(:end_date, 'YYYY-MM-DD')
and   sl.ledger_type_code = '505'
and   sl.location_id = :coa_short
and   il.cost_centre_id = sl.sub_ldgr_item_code
and   il.store_id = st.store_id
and   il.item_id  = it.item_id
and   il.move_type_id = mt.move_type_id
and   il.move_type_id in ('16','2')
and   il.store_id <> '10110'
and   il.store_id not in (select s.store_id from item.store s where s.main_sub = 'S')
group by sl.location_id, il.move_type_id, il.store_id, st.description , il.cost_centre_id, sl.sub_ldgr_item_desc, il.item_id, it.description
order by il.store_id
        '''

        cursor.execute(query, {
            'start_date': start_date,
            'end_date': end_date,
            'coa_short': coa_short,

        })

        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]

        # Create an in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()



        # Add headers
        for col, header in enumerate(columns):
            worksheet.write(0, col, header)

        # Write data
        for row, data in enumerate(cursor, start=1):
            for col, value in enumerate(data):
                    worksheet.write(row, col, value)

        workbook.close()
        output.seek(0)

        cursor.close()
        connection.close()

        return send_file(
            output,
            as_attachment=True,
            download_name=f'consumption_analysis_{start_date}_to_{end_date}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500