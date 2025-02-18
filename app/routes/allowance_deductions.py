from flask import Blueprint, jsonify, request, send_file, Response
from flask_cors import CORS
from app.db import get_db_connection
import io
import xlsxwriter

ad_bp = Blueprint("ad", __name__)
CORS(ad_bp)


@ad_bp.route('/ad', methods=['POST'])
def ad():
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')

    if not start_date or not end_date:
        return jsonify({"error": "Missing start_date or end_date in request body"}), 400

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
        select par.location_id, par.mrno, i.NAME, i.DEPARTMENT, i.DESIGNATION, 
               dar.arrear_code code, dar.description, 
               to_char(par.end_date,'Mon-RR') Month, 
               par.amount, i.JOINING_DATE, i.NIC
        from payroll.pay_arrear par, payroll.def_arrear dar, hrd.vu_information i
        where par.arrear_code = dar.arrear_code
        and   par.mrno = i.MRNO
        and   par.amount > 0
        and   par.location_id = NVL(NULL, par.location_id)
        and   par.end_date >= :start_date
        and   par.end_date <= :end_date
        union
        select pad.location_id, pad.mrno, i.NAME, i.DEPARTMENT, i.DESIGNATION, 
               dad.ad_code code, dad.description, 
               to_char(pad.end_date,'Mon-RR') Month, 
               pad.calc_amount amount, i.JOINING_DATE, i.NIC
        from payroll.pay_allowance_deduction pad, 
             payroll.def_allowance_deduction dad, 
             hrd.vu_information i
        where pad.ad_code = dad.ad_code
        and   pad.mrno = i.MRNO
        and   pad.calc_amount > 0
        and   dad.ad_code not in ('000')
        and   pad.location_id = NVL(NULL, pad.location_id)
        and   pad.end_date >= :start_date
        and   pad.end_date <= :end_date
        order by description, Month, mrno
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
            if header in ['NAME', 'DEPARTMENT', 'DESIGNATION', 'DESCRIPTION']:
                worksheet.set_column(col, col, 30)  # Wider for text columns
            elif header in ['AMOUNT']:
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
                if column_name == 'JOINING_DATE':
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

        filename = f"allowance-deductions_{start_date}_to_{end_date}.xlsx"

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