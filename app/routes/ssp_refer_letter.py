from flask import Blueprint, jsonify, request, send_file
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

ssp_bp = Blueprint("ssp", __name__)
CORS(ssp_bp, resources={
    r"/ssp": {
        "origins": "*",
        "methods": ["GET", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

@ssp_bp.route('/ssp', methods=['GET', 'OPTIONS'])
def ssp():
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
            Select td.client_id, c.name client_name, td.mrno, p.name, 
                   td.trans_no, td.admission_no, td.ref_letter_no, 
                   lm.client_ref_no, lm.trans_date ref_letter_trans_date, 
                   sum(td.dr_amount-td.cr_amount) Amount
            From finance.pbs_tran_detail td, BILLING.REF_LETTER_MASTER LM, 
                 registration.v_patient p, billing.client c
            Where td.client_id = '1012000041'
            and  td.coa_code = '911010'
            and  td.client_id = c.client_id
            and  td.REF_LETTER_NO IS NOT NULL
            and  td.REF_LETTER_NO = LM.REF_LETTER_NO
            and  lm.mrno = p.mrno
            Group by td.mrno, td.admission_no, td.ref_letter_no, 
                     lm.client_ref_no, p.name, lm.trans_date, 
                     td.trans_no, td.client_id, c.name
            order by lm.trans_date
        '''

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
                if columns[col].upper() == 'REF_LETTER_TRANS_DATE':
                    worksheet.write(row, col, value, date_format)
                else:
                    worksheet.write(row, col, value)

        workbook.close()
        output.seek(0)

        cursor.close()
        connection.close()

        # Add cache control headers
        response = send_file(
            output,
            as_attachment=True,
            download_name='ssp_refer_letter.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response

    except Exception as e:
        return jsonify({"error": str(e)}), 500
