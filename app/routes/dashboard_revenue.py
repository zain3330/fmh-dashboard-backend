from flask import Blueprint, jsonify
from app.db import get_db_connection

revenue_bp = Blueprint("revenue", __name__)


@revenue_bp.route('/revenue', methods=['GET'])
def revenue():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()



        ipd_revenue = '''
    SELECT in_Setup, SUM(amount) AMOUNT
FROM (
    SELECT im.admission_no, imbd.serial_no, 
           im.mrno, p.name AS Pat_Name, im.invoice_date AS trns_date, 
           im.invoice_no, imbd.contract_id, imbd.item_id, 
           Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(imbd.item_id) AS Drug, 
           imbd.qty, imbd.amount, imbd.client_id AS client_id, 
           opa.admission_final_time, opa.discharge_date, cl.name AS CL_Name, 
           ol.description AS order_location, doc.NAME AS Adm_Doctor, 
           doc.DEPARTMENT AS Adm_Department, pt.description AS Patient_Type, 
           opa.order_admission_type AS admission_type, 
           ins.income_description AS in_Setup, 
           imbd.department_id, gsl.sub_ldgr_item_desc AS sub_ldgr_desc
    FROM BILLING.INVOICE_MASTER im
    JOIN BILLING.INVOICE_MASTER_BILL_DIST imbd ON im.invoice_no = imbd.invoice_no
    JOIN registration.v_patient p ON im.mrno = p.mrno
    JOIN orderentry.order_patient_admission opa ON im.mrno = opa.mrno AND im.admission_no = opa.admission_no
    LEFT JOIN billing.client cl ON imbd.client_id = cl.client_id
    JOIN definitions.order_location ol ON im.location_id = ol.location_id AND im.order_location_id = ol.order_location_id
    JOIN definitions.v_doctor doc ON opa.doctor_id = doc.doctor_id
    JOIN ORDERENTRY.ORDER_MASTER om ON om.order_type_id = opa.order_type_id 
                                   AND om.order_no = opa.order_no 
                                   AND om.location_id = opa.location_id 
                                   AND om.order_location_id = opa.order_location_id
    JOIN definitions.patient_type pt ON om.patient_type_id = pt.patient_type_id
    JOIN billing.income_setup ins ON ins.income_id = imbd.income_id
    LEFT JOIN finance.gl_sub_ledgers gsl ON imbd.department_id = gsl.sub_ldgr_item_code
    JOIN billing.final_invoice_master fim ON im.admission_no = fim.admission_no
    WHERE fim.final_invoice_date >= SYSDATE - 30
    AND ol.description NOT LIKE 'ADULT/PAEDS-EMERGENCY - FMH'
    AND im.admission_no IS NOT NULL

    UNION ALL

    SELECT rm.admission_no, rmbd.serial_no, 
           rm.mrno, p.name AS Pat_Name, rm.return_date AS trns_date, 
           rm.invoice_no, rmbd.contract_id, rmbd.item_id, 
           Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(rmbd.item_id) AS Drug, 
           -1 * rmbd.qty, -1 * rmbd.amount, 
           rmbd.contract_id, opa.admission_final_time, opa.discharge_date, cl.name AS CL_Name, 
           ol.description AS order_location, doc.NAME AS Adm_Doctor, 
           doc.DEPARTMENT AS Adm_Department, pt.description AS Patient_Type, 
           opa.order_admission_type AS admission_type, 
           ins.income_description AS in_Setup, 
           rmbd.department_id, gsl.sub_ldgr_item_desc AS sub_ldgr_desc
    FROM BILLING.RETURN_MASTER rm
    JOIN BILLING.RETURN_MASTER_BILL_DIST rmbd ON rm.return_no = rmbd.return_no
    JOIN registration.v_patient p ON rm.mrno = p.mrno
    JOIN orderentry.order_patient_admission opa ON rm.mrno = opa.mrno AND rm.admission_no = opa.admission_no
    LEFT JOIN billing.client cl ON rmbd.client_id = cl.client_id
    JOIN definitions.order_location ol ON rm.location_id = ol.location_id AND rm.order_location_id = ol.order_location_id
    JOIN definitions.v_doctor doc ON opa.doctor_id = doc.doctor_id
    JOIN ORDERENTRY.ORDER_MASTER om ON om.order_type_id = opa.order_type_id 
                                   AND om.order_no = opa.order_no 
                                   AND om.location_id = opa.location_id 
                                   AND om.order_location_id = opa.order_location_id
    JOIN definitions.patient_type pt ON om.patient_type_id = pt.patient_type_id
    JOIN billing.income_setup ins ON ins.income_id = rmbd.income_id
    LEFT JOIN finance.gl_sub_ledgers gsl ON rmbd.department_id = gsl.sub_ldgr_item_code
    JOIN billing.final_invoice_master fim ON rm.admission_no = fim.admission_no
    WHERE fim.final_invoice_date >= SYSDATE - 30
    AND ol.description NOT LIKE 'ADULT/PAEDS-EMERGENCY - FMH'
    AND rm.admission_no IS NOT NULL
) 
GROUP BY in_Setup
ORDER BY in_Setup

          '''
        ear_revenue='''
        SELECT in_Setup, SUM(amount) AS AMOUNT
FROM (
    SELECT im.admission_no, imbd.serial_no, NULL AS Return_no,
           im.mrno, p.name AS Pat_Name, im.invoice_date AS trns_date, im.invoice_no, imbd.contract_id,
           imbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(imbd.item_id) AS Drug,
           imbd.qty, imbd.amount, imbd.client_id AS client_id, opa.admission_final_time, opa.discharge_date,
           cl.name AS CL_Name, ol.description AS order_location, doc.NAME AS Adm_Doctor, doc.DEPARTMENT AS Adm_Department,
           pt.description AS Patient_Type, opa.order_admission_type AS admission_type, ins.income_description AS in_Setup,
           imbd.department_id, gsl.sub_ldgr_item_desc AS sub_ldgr_desc
    FROM BILLING.INVOICE_MASTER im
    JOIN BILLING.INVOICE_MASTER_BILL_DIST imbd ON im.INVOICE_NO = imbd.INVOICE_NO
    JOIN registration.v_patient p ON im.Mrno = p.mrno
    JOIN orderentry.order_patient_admission opa ON im.mrno = opa.mrno AND im.admission_no = opa.admission_no
    LEFT JOIN billing.client cl ON imbd.client_id = cl.client_id
    JOIN definitions.order_location ol ON im.Location_Id = ol.location_id AND im.Order_Location_Id = ol.order_location_id
    JOIN definitions.v_doctor doc ON opa.doctor_id = doc.DOCTOR_ID
    JOIN ORDERENTRY.ORDER_MASTER om ON om.ORDER_TYPE_ID = opa.ORDER_TYPE_ID AND om.ORDER_NO = opa.ORDER_NO 
                                     AND om.LOCATION_ID = opa.LOCATION_ID AND om.ORDER_LOCATION_ID = opa.ORDER_LOCATION_ID
    JOIN definitions.patient_type pt ON om.patient_type_id = pt.patient_type_id
    JOIN billing.income_setup ins ON ins.income_id = imbd.income_id
    LEFT JOIN finance.gl_sub_ledgers gsl ON imbd.DEPARTMENT_ID = gsl.sub_ldgr_item_code
    WHERE ol.description = 'ADULT/PAEDS-EMERGENCY - FMH'
      AND im.admission_no IS NOT NULL
      AND im.admission_no IN (SELECT admission_no FROM billing.final_invoice_master WHERE final_invoice_date >= sysdate - 30)
    
    UNION ALL
    
    SELECT rm.admission_no, rmbd.serial_no, rmbd.return_no,
           rm.mrno, p.name AS Pat_Name, rm.return_date AS trns_date, rm.invoice_no, rmbd.contract_id,
           rmbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(rmbd.item_id) AS Drug, 
           -1 * rmbd.qty, -1 * rmbd.amount, rmbd.contract_id, opa.admission_final_time, opa.discharge_date,
           cl.name AS CL_Name, ol.description AS order_location, doc.NAME AS Adm_Doctor, doc.DEPARTMENT AS Adm_Department,
           pt.description AS Patient_Type, opa.order_admission_type AS admission_type, ins.income_description AS in_Setup,
           rmbd.department_id, gsl.sub_ldgr_item_desc AS sub_ldgr_desc
    FROM BILLING.RETURN_MASTER rm
    JOIN BILLING.RETURN_MASTER_BILL_DIST rmbd ON rm.RETURN_NO = rmbd.RETURN_NO
    JOIN registration.v_patient p ON rm.Mrno = p.mrno
    JOIN orderentry.order_patient_admission opa ON rm.mrno = opa.mrno AND rm.admission_no = opa.admission_no
    LEFT JOIN billing.client cl ON rmbd.client_id = cl.client_id
    JOIN definitions.order_location ol ON rm.Location_Id = ol.location_id AND rm.Order_Location_Id = ol.order_location_id
    JOIN definitions.v_doctor doc ON opa.doctor_id = doc.DOCTOR_ID
    JOIN ORDERENTRY.ORDER_MASTER om ON om.ORDER_TYPE_ID = opa.ORDER_TYPE_ID AND om.ORDER_NO = opa.ORDER_NO 
                                     AND om.LOCATION_ID = opa.LOCATION_ID AND om.ORDER_LOCATION_ID = opa.ORDER_LOCATION_ID
    JOIN definitions.patient_type pt ON om.patient_type_id = pt.patient_type_id
    JOIN billing.income_setup ins ON ins.income_id = rmbd.income_id
    LEFT JOIN finance.gl_sub_ledgers gsl ON rmbd.DEPARTMENT_ID = gsl.sub_ldgr_item_code
    WHERE ol.description = 'ADULT/PAEDS-EMERGENCY - FMH'
      AND rm.admission_no IS NOT NULL
      AND rm.admission_no IN (SELECT admission_no FROM billing.final_invoice_master WHERE final_invoice_date >= sysdate - 30)
)
GROUP BY in_Setup
ORDER BY in_Setup

        '''

        opd_revenue='''
        SELECT in_Setup, SUM(amount) AS Total_Amt
FROM (
    SELECT 
        im.admission_no, imbd.serial_no, NULL AS Return_no,
        im.mrno, p.name AS Pat_Name, im.invoice_date AS trns_date, im.invoice_no,
        imbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(imbd.item_id) AS Drug,
        imbd.qty, imbd.amount, pt.description AS Patient_Type, cl.name AS CL_Name, 
        gsl.sub_ldgr_item_desc AS sub_ldgr_desc, doc.NAME AS Doctor, doc.DEPARTMENT AS Department,
        ins.income_description AS in_Setup
    FROM BILLING.INVOICE_MASTER im
    JOIN BILLING.INVOICE_MASTER_BILL_DIST imbd ON im.INVOICE_NO = imbd.INVOICE_NO
    JOIN registration.v_patient p ON im.mrno = p.mrno
    LEFT JOIN billing.client cl ON imbd.client_id = cl.client_id
    LEFT JOIN ORDERENTRY.ORDER_MASTER om 
        ON om.ORDER_TYPE_ID = im.ORDER_TYPE_ID 
        AND om.ORDER_NO = im.ORDER_NO 
        AND om.LOCATION_ID = im.LOCATION_ID 
        AND om.ORDER_LOCATION_ID = im.ORDER_LOCATION_ID
    LEFT JOIN definitions.v_doctor doc ON om.reffering_inhouse_doctor_id = doc.DOCTOR_ID
    JOIN billing.income_setup ins ON imbd.income_id = ins.income_id
    JOIN definitions.patient_type pt ON om.patient_type_id = pt.patient_type_id
    LEFT JOIN finance.gl_sub_ledgers gsl ON IMBD.DEPARTMENT_ID = gsl.sub_ldgr_item_code
    WHERE im.invoice_date >= SYSDATE - 30
    AND im.admission_no IS NULL

    UNION ALL

    SELECT 
        rm.admission_no, rmbd.serial_no, rmbd.return_no,
        rm.mrno, p.name AS Pat_Name, rm.return_date AS trns_date, rm.invoice_no,
        rmbd.item_id, Pharmacy.pkg_common.GET_GENERIC_BRAND_DETAIL(rmbd.item_id) AS Drug,
        -1 * rmbd.qty, -1 * rmbd.amount, pt.description AS Patient_Type, cl.name AS CL_Name, 
        gsl.sub_ldgr_item_desc AS sub_ldgr_desc, doc.NAME AS Doctor, doc.DEPARTMENT AS Department,
        ins.income_description AS in_Setup
    FROM BILLING.RETURN_MASTER rm
    JOIN BILLING.RETURN_MASTER_BILL_DIST rmbd ON rm.RETURN_NO = rmbd.RETURN_NO
    JOIN registration.v_patient p ON rm.mrno = p.mrno
    LEFT JOIN ORDERENTRY.ORDER_MASTER om 
        ON om.ORDER_TYPE_ID = rm.ORDER_TYPE_ID 
        AND om.ORDER_NO = rm.ORDER_NO 
        AND om.LOCATION_ID = rm.LOCATION_ID 
        AND om.ORDER_LOCATION_ID = rm.ORDER_LOCATION_ID
    LEFT JOIN definitions.v_doctor doc ON om.reffering_inhouse_doctor_id = doc.DOCTOR_ID
    JOIN billing.income_setup ins ON rmbd.income_id = ins.income_id
    JOIN definitions.patient_type pt ON om.patient_type_id = pt.patient_type_id
    LEFT JOIN billing.client cl ON rmbd.client_id = cl.client_id
    LEFT JOIN finance.gl_sub_ledgers gsl ON rmbd.DEPARTMENT_ID = gsl.sub_ldgr_item_code
    WHERE rm.return_date >= SYSDATE - 30
    AND rm.admission_no IS NULL
) tmp
GROUP BY in_Setup
ORDER BY in_Setup

        '''


        # Execute opd_revenue query
        cursor.execute(opd_revenue)
        opd_results = cursor.fetchall()
        opd_revenue = {row[0]: float(row[1]) for row in opd_results}

        # Execute ipd_revenue query
        cursor.execute(ipd_revenue)
        ipd_results = cursor.fetchall()
        ipd_revenue = {row[0]: float(row[1]) for row in ipd_results}

        # Execute ear_revenue query
        cursor.execute(ear_revenue)
        ear_results = cursor.fetchall()
        ear_revenue = {row[0]: float(row[1]) for row in ear_results}

        revenue_data  = {

            "ipd_revenue": ipd_revenue,
            "ear_revenue": ear_revenue,
            "opd_revenue": opd_revenue,

  }

        cursor.close()
        connection.close()

        return jsonify(revenue_data )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
