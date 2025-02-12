from flask import Blueprint, Response
import io
import xlsxwriter
from app.db import get_db_connection
daz_bp = Blueprint("daz", __name__)

@daz_bp.route('/daz', methods=['GET'])
def daz():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
         select fm.client_id, cl.name Client_Name, fm.process_id, fm.final_invoice_date, fm.client_invoice_no,
       (select min(lm.client_ref_no)
        from  finance.pbs_tran_detail_corporate ptdc, billing.ref_letter_master lm
        where ptdc.ref_letter_no is not null
        and   ptdc.process_id = fm.process_id
        and   ptdc.client_id  = fm.client_id
        and   ptdc.final_invoice_no = fm.client_invoice_no
        and   ptdc.mrno = p.mrno
        and   ptdc.ref_letter_no = lm.ref_letter_no) ref_letter_no,
       fm.mrno, p.nic_new,
       (select max(ptdc.admission_no)
        from  finance.pbs_tran_detail_corporate ptdc
        where ptdc.process_id = fm.process_id
        and   ptdc.client_id  = fm.client_id
        and   ptdc.final_invoice_no = fm.client_invoice_no
        and   ptdc.mrno = p.mrno) admission_no,

       (select max(fim.admission_date)
        from  finance.pbs_tran_detail_corporate ptdc, billing.final_invoice_master fim
        where ptdc.process_id = fm.process_id
        and   ptdc.client_id  = fm.client_id
        and   ptdc.final_invoice_no = fm.client_invoice_no
        and   ptdc.mrno = p.mrno
        and   ptdc.admission_no = fim.admission_no
        and   ptdc.mrno         = fim.mrno) admission_date,

       p.name Patient_Name, fm.net_receivable, fm.received_amount, (nvl(fm.net_receivable,0)-nvl(fm.received_amount,0)) remaining

from billing.final_invoice_master fm, billing.client cl, registration.v_patient p
where fm.client_id=cl.client_id
and fm.mrno=p.mrno
and fm.client_id is not null
and fm.mrno is not null
and ABS (round(nvl(fm.net_receivable,0)-nvl(fm.received_amount,0)))=0
and (fm.process_id, fm.client_id) in (select distinct process_id, client_id from finance.pbs_tran_detail_corporate)
order by 1,4
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
                if columns[col].upper() in ['FINAL_INVOICE_DATE', 'ADMISSION_DATE']:  # Apply date format
                    worksheet.write(row, col, value, date_format)
                else:
                    worksheet.write(row, col, value)

        workbook.close()
        output.seek(0)

        cursor.close()
        connection.close()

        return Response(
            output.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=debtor_aging_zero.xlsx"}
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
