from flask import Blueprint, jsonify, request
from app.db import get_db_connection

from flask_cors import CORS

er_bp = Blueprint("er", __name__)
CORS(er_bp)


@er_bp.route('/er', methods=['POST'])
def er():
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
  -------------EAR REVENUE----------------
SELECT  Adm_Doctor, Adm_Department, sub_ldgr_desc, Patient_Type, Cl_name, in_Setup, Count(DISTINCT invoice_no) Invoice_Count, SUM(amount) Receivable
FROM
(
SELECT im.admission_no, imbd.serial_no, NULL Return_no,
       im.mrno, p.name Pat_Name, im.invoice_date trns_date, im.invoice_no, imbd.contract_id,
       imbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(imbd.item_id) Drug,
       imbd.qty, imbd.amount, imbd.client_id client_id, opa.admission_final_time, opa.discharge_date,
       cl.name CL_Name, ol.description order_location, doc.NAME Adm_Doctor, doc.DEPARTMENT Adm_Department, pt.description Patient_Type,
       opa.order_admission_type admission_type,  ins.income_description in_Setup, imbd.department_id, gsl.sub_ldgr_item_desc sub_ldgr_desc
  FROM BILLING.INVOICE_MASTER    IM,
       BILLING.INVOICE_MASTER_BILL_DIST IMBD,
       registration.v_patient p,
       orderentry.order_patient_admission opa,
       billing.client cl,
       definitions.order_location ol,
       definitions.v_doctor doc,
       ORDERENTRY.ORDER_MASTER   OM,
       definitions.patient_type pt,
       billing.income_setup ins,
       finance.gl_sub_ledgers gsl
 WHERE IM.INVOICE_NO    =  IMBD.INVOICE_NO
  AND LOWER(doc.NAME) LIKE :name
              AND LOWER(doc.DEPARTMENT) LIKE :department
              AND LOWER(gsl.sub_ldgr_item_desc) LIKE :des
              AND LOWER(pt.description) LIKE :patient_type
   AND IM.Mrno      = p.mrno
   and im.mrno = opa.mrno
   and im.admission_no = opa.admission_no
   and imbd.client_id(+) = cl.client_id
   AND im.Location_Id = ol.location_id
   AND im.Order_Location_Id = ol.order_location_id
   AND opa.doctor_id = doc.DOCTOR_ID
   AND OM.ORDER_TYPE_ID = OPA.ORDER_TYPE_ID
   AND OM.ORDER_NO      = OPA.ORDER_NO
   AND OM.LOCATION_ID   = OPA.LOCATION_ID
   AND OM.ORDER_LOCATION_ID = OPA.ORDER_LOCATION_ID
   AND om.patient_type_id = pt.patient_type_id
   AND ins.income_id = imbd.income_id
   AND UPPER(ol.description) like 'ADULT/PAEDS-EMERGENCY - FMH'
   AND IMBD.DEPARTMENT_ID = gsl.sub_ldgr_item_code(+)
   --and imbd.department_id='1010365'
   --AND im.admission_no = '10122000030996'
   and im.admission_no is not null
   AND im.admission_no IN
   (select fim.admission_no
    from billing.final_invoice_master fim
where fim.final_invoice_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
               and fim.final_invoice_date < TO_DATE(:end_date, 'YYYY-MM-DD'))
   /*AND IMBD.INCOME_ID in '8'*/
union
SELECT rm.admission_no, rmbd.serial_no, rmbd.return_no,
       rm.mrno, p.name Pat_Name, rm.return_date trns_date, rm.invoice_no, rmbd.contract_id,
       rmbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(rmbd.item_id) Drug, -1*rmbd.qty, -1*rmbd.amount,
       rmbd.contract_id, opa.admission_final_time, opa.discharge_date, cl.name CL_Name,
       ol.description order_location, doc.NAME Adm_Doctor, doc.DEPARTMENT Adm_Department, pt.description Patient_Type,
       opa.order_admission_type admission_type, ins.income_description in_Setup, rmbd.department_id, gsl.sub_ldgr_item_desc sub_ldgr_desc

  FROM BILLING.RETURN_MASTER    RM,
       BILLING.RETURN_MASTER_BILL_DIST RMBD,
       registration.v_patient p,
       orderentry.order_patient_admission opa,
       billing.client cl,
       definitions.order_location ol,
       definitions.v_doctor doc,
       ORDERENTRY.ORDER_MASTER   OM,
       definitions.patient_type pt,
       billing.income_setup ins,
       finance.gl_sub_ledgers gsl
 WHERE RM.RETURN_NO    =  RMBD.RETURN_NO
 AND LOWER(doc.NAME) LIKE :name
              AND LOWER(doc.DEPARTMENT) LIKE :department
              AND LOWER(gsl.sub_ldgr_item_desc) LIKE :des
              AND LOWER(pt.description) LIKE :patient_type
   AND RM.Mrno      = p.mrno
   and rm.mrno = opa.mrno
   and rm.admission_no = opa.admission_no
   and rmbd.client_id(+) = cl.client_id
   AND rm.Location_Id = ol.location_id
   AND rm.Order_Location_Id = ol.order_location_id
   AND opa.doctor_id = doc.DOCTOR_ID
   AND OM.ORDER_TYPE_ID = OPA.ORDER_TYPE_ID
   AND OM.ORDER_NO      = OPA.ORDER_NO
   AND OM.LOCATION_ID   = OPA.LOCATION_ID
   AND OM.ORDER_LOCATION_ID = OPA.ORDER_LOCATION_ID
   AND om.patient_type_id = pt.patient_type_id
   AND ins.income_id = rmbd.income_id
   AND UPPER(ol.description) like 'ADULT/PAEDS-EMERGENCY - FMH'
   AND rMBD.DEPARTMENT_ID = gsl.sub_ldgr_item_code(+)
   and rm.admission_no is not null
   AND rm.admission_no IN
   (select fim.admission_no
    from billing.final_invoice_master fim
where fim.final_invoice_date >= TO_DATE(:start_date, 'YYYY-MM-DD')
               and fim.final_invoice_date < TO_DATE(:end_date, 'YYYY-MM-DD'))
   ---and rmbd.department_id='1010365'
   --AND rm.admission_no = '10122000030996'
   /*AND RMBD.INCOME_ID in '8'*/)
GROUP BY Adm_Doctor, Adm_Department, Patient_Type, Cl_name, in_Setup, sub_ldgr_desc
order by Adm_Department,in_Setup
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
