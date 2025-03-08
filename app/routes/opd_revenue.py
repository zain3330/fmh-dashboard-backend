from flask import Blueprint, jsonify, request
from app.db import get_db_connection

from flask_cors import CORS

or_bp = Blueprint("or", __name__)
CORS(or_bp)


@or_bp.route('/or', methods=['POST'])
def opd_r():
    data = request.get_json()
    start_date = data.get('startDate')
    end_date = data.get('endDate')
    name = data.get('name')
    des = data.get('des')
    department = data.get('department')
    patient_type = data.get('patient_type')

    if not start_date or not end_date:
        return jsonify({"error": "Missing required parameters"}), 400
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
 ------------OPD REVENUE-------------------
SELECT Doctor, Department, sub_ldgr_desc, Patient_Type, CL_Name, in_Setup, Count(DISTINCT invoice_no) Invoice_Count, SUM(amount) Total_Amt
FROM
(
SELECT im.admission_no, imbd.serial_no, NULL Return_no,
       im.mrno, p.name Pat_Name, im.invoice_date trns_date, im.invoice_no,
       imbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(imbd.item_id) Drug, imbd.qty, imbd.amount,
       doc.NAME Doctor, doc.DEPARTMENT Department, pt.description Patient_Type, cl.name CL_Name, gsl.sub_ldgr_item_desc sub_ldgr_desc,
       ins.income_description in_Setup
  FROM BILLING.INVOICE_MASTER    IM,
       BILLING.INVOICE_MASTER_BILL_DIST IMBD,
       registration.v_patient p,
       definitions.v_doctor doc,
       ORDERENTRY.ORDER_MASTER   OM,
       billing.income_setup ins,
       definitions.patient_type pt,
       billing.client cl,
       finance.gl_sub_ledgers gsl
 WHERE IM.INVOICE_NO    =  IMBD.INVOICE_NO
    AND LOWER(doc.NAME) LIKE :name
     AND LOWER(doc.DEPARTMENT) LIKE :department
    AND LOWER(gsl.sub_ldgr_item_desc) LIKE :des
    AND LOWER(pt.description) LIKE :patient_type
   AND IM.Mrno      = p.mrno
   and imbd.client_id(+) = cl.client_id
   AND om.reffering_inhouse_doctor_id = doc.DOCTOR_ID(+)
   AND OM.ORDER_TYPE_ID = IM.ORDER_TYPE_ID
   AND OM.ORDER_NO      = IM.ORDER_NO
   AND OM.LOCATION_ID   = IM.LOCATION_ID
   AND OM.ORDER_LOCATION_ID = IM.ORDER_LOCATION_ID
   AND ins.income_id = imbd.income_id
   AND om.patient_type_id = pt.patient_type_id
   AND IMBD.DEPARTMENT_ID = gsl.sub_ldgr_item_code(+)
  and im.invoice_date >=  TO_DATE(:start_date,'YYYY-MM-DD')
    and  im.invoice_date  <  TO_DATE(:end_date,'YYYY-MM-DD')
   and im.admission_no is null
union
SELECT rm.admission_no, rmbd.serial_no, rmbd.return_no,
       rm.mrno, p.name Pat_Name, rm.return_date trns_date, rm.invoice_no,
       rmbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(rmbd.item_id) Drug, -1*rmbd.qty, -1*rmbd.amount,
       doc.NAME Doctor, doc.DEPARTMENT Department, pt.description Patient_Type, cl.name CL_Name, gsl.sub_ldgr_item_desc sub_ldgr_desc,
       ins.income_description in_Setup
  FROM BILLING.RETURN_MASTER    RM,
       BILLING.RETURN_MASTER_BILL_DIST RMBD,
       registration.v_patient p,
       definitions.v_doctor doc,
       ORDERENTRY.ORDER_MASTER   OM,
       billing.income_setup ins,
       definitions.patient_type pt,
       billing.client cl,
       finance.gl_sub_ledgers gsl
   WHERE RM.RETURN_NO    =  RMBD.RETURN_NO
    AND LOWER(doc.NAME) LIKE :name
    AND LOWER(doc.DEPARTMENT) LIKE :department
    AND LOWER(gsl.sub_ldgr_item_desc) LIKE :des
    AND LOWER(pt.description) LIKE :patient_type
   AND RM.Mrno      = p.mrno
   AND om.reffering_inhouse_doctor_id = doc.DOCTOR_ID(+)
   AND ins.income_id = rmbd.income_id
   and Rmbd.client_id(+) = cl.client_id
   AND OM.ORDER_TYPE_ID = RM.ORDER_TYPE_ID
   AND OM.ORDER_NO      = RM.ORDER_NO
   AND OM.LOCATION_ID   = RM.LOCATION_ID
   AND OM.ORDER_LOCATION_ID = RM.ORDER_LOCATION_ID
   and rm.admission_no is null
   AND om.patient_type_id = pt.patient_type_id
   AND RMBD.DEPARTMENT_ID = gsl.sub_ldgr_item_code(+)
   and rm.return_date  >=  TO_DATE(:start_date,'YYYY-MM-DD')
    and   rm.return_date  < TO_DATE(:end_date,'YYYY-MM-DD'))
GROUP BY Doctor, Department, in_Setup, Patient_Type, CL_Name, sub_ldgr_desc
order by Department
        '''

        cursor.execute(query, {
            'start_date': start_date,
            'end_date': end_date,
            'name': f'%{name.lower()}%' if name else '%',
            'department': f'%{department.lower()}%' if department else '%',
            'des': f'%{des.lower()}%' if des else '%',
            'patient_type': f'%{patient_type.lower()}%' if patient_type else '%'
        })

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        result = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
