from flask import Blueprint, jsonify, request, send_file, Response
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

ld_bp = Blueprint("ld", __name__)
CORS(ld_bp)


@ld_bp.route('/ld', methods=['POST'])
def ld():
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')

    if not start_date or not end_date:
        return jsonify({"error": "Missing start_date or end_date in request body"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
 select l.description, lrd.end_date, to_char(lrd.end_date,'Mon-RR') Month, lt.description Loan_Type, lrd.mrno, i.NAME, i.DESIGNATION, i.DEPARTMENT, lrd.loan_amount, lrd.refund_amount
from payroll.loan_refund_detail lrd, payroll.loan_payment_master lpm, payroll.def_loan_type lt,
     hrd.v_information i, definitions.location l
where lt.loan_code = lpm.loan_code
and   lt.location_id = '101'
and   lpm.loan_location_id = l.location_id
and   lpm.mrno = i.mrno
and   lpm.loan_no = lrd.loan_no
and   lrd.end_date >= :start_date
and   lrd.end_date <= :end_date
order by l.description, lrd.mrno, lt.description
        '''

        cursor.execute(query, {
            'start_date': start_date,
            'end_date': end_date
        })

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()

        # Create an in-memory Excel file
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        worksheet = workbook.add_worksheet()

        # Create formats
        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#D3D3D3'
        })

        date_format = workbook.add_format({
            'num_format': 'dd-mmm-yyyy'
        })

        number_format = workbook.add_format({
            'num_format': '#,##0.00'  # Format for amount with 2 decimal places
        })

        # Add headers and set column widths
        for col, header in enumerate(columns):
            worksheet.write(0, col, header, header_format)

            # Set specific column widths based on content type
            if header in ['NAME', 'DEPARTMENT', 'DESIGNATION', 'DESCRIPTION','LOAN_TYPE']:
                worksheet.set_column(col, col, 30)  # Wider for text columns
            elif header in ['LOAN_AMOUNT','REFUND_AMOUNT']:
                worksheet.set_column(col, col, 12)  # Medium for amounts
            else:
                worksheet.set_column(col, col, 15)  # Default width

        # Add data rows with proper formatting
        for row_idx, row in enumerate(rows, start=1):
            for col_idx, value in enumerate(row):
                column_name = columns[col_idx]

                if value is None:
                    worksheet.write(row_idx, col_idx, '')
                    continue

                # Apply specific formatting based on column type
                if column_name == 'END_DATE':
                    worksheet.write_datetime(row_idx, col_idx, value, date_format)

                else:
                    worksheet.write(row_idx, col_idx, str(value))

        # Add autofilter
        worksheet.autofilter(0, 0, len(rows), len(columns) - 1)

        # Freeze the top row
        worksheet.freeze_panes(1, 0)

        workbook.close()
        output.seek(0)

        # Clean up database resources
        cursor.close()
        connection.close()

        filename = f"loan-deductions_{start_date}_to_{end_date}.xlsx"

        return Response(
            output.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        # Clean up resources in case of error
        if 'cursor' in locals():
            cursor.close()
        if 'connection' in locals():
            connection.close()
        if 'output' in locals():
            output.close()
        return jsonify({"error": str(e)}), 500