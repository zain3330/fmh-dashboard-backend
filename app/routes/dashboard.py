from flask import Blueprint, jsonify
from app.db import get_db_connection

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route('/dashboard', methods=['GET'])
def dashboard():
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        # Total Debtor Query
        debtor_query = '''
        SELECT sum(NVL(FM.NET_RECEIVABLE, 0) - NVL(FM.RECEIVED_AMOUNT, 0)) AS total_receivable
        FROM BILLING.FINAL_INVOICE_MASTER FM, BILLING.CLIENT CL, REGISTRATION.V_PATIENT P
        WHERE FM.CLIENT_ID = CL.CLIENT_ID
        AND FM.MRNO = P.MRNO
        AND FM.CLIENT_ID IS NOT NULL
        AND NVL(ABS(FM.NET_RECEIVABLE), 0) - NVL(FM.RECEIVED_AMOUNT, 0) > 0
        AND FM.MRNO IS NOT NULL
        AND FM.CLIENT_INVOICE_NO IN
        (SELECT FIM.FINAL_INVOICE_NO
        FROM BILLING.FINAL_INVOICE_MASTER FIM
        WHERE NVL(FIM.NET_RECEIVABLE, 0) > NVL(FIM.RECEIVED_AMOUNT, 0)
        AND FIM.FINAL_INVOICE_TYPE IN ('R', 'H')
        AND FIM.FINAL_INVOICE_DATE > '01-JAN-2016')
        AND FM.FINAL_INVOICE_TYPE IN ('I', 'O', 'H')
        '''

        # Consumption Analysis Query
        consumption_query = '''
        Select sum(NVL(il.qty_cr,0)-NVL(il.qty_dr,0)) AS consumption_qty,
               (SUM((NVL(il.qty_cr,0)-NVL(il.qty_dr,0))*(il.unit_cost))) AS consumption_value
        from mms.mms_item_ledger il, item.store st, item.item it, mms.def_move_type mt, FINANCE.GL_SUB_LEDGERS sl
        where il.trans_date >= sysdate-30
        and   sl.ledger_type_code = '505'
        and   sl.location_id = '101'
        and   il.cost_centre_id = sl.sub_ldgr_item_code
        and   il.store_id = st.store_id
        and   il.item_id  = it.item_id
        and   il.move_type_id = mt.move_type_id
        and   il.move_type_id in ('16','2')
        and   il.store_id <> '10110'
        and   il.store_id not in (select s.store_id from item.store s where s.main_sub = 'S')
        '''

        # Client Receipts Query
        receipts_query = '''
        select sum(crd.amount+nvl(crd.wht_tax,0)) AS gross_amount
        from billing.cash_receive_master crm, billing.cash_receive_detail crd, billing.client c,
             hrd.vu_information i, billing.payment_mode pm
        where crm.receive_no = crd.receive_no
        and   crm.client_id  = c.client_id
        and   crm.received_by = i.MRNO
        and   crm.receive_date >= sysdate-30
        and   crd.payment_mode_id = pm.payment_mode_id
        and crm.receive_no not in (select crm.receipt_no from billing.cash_refund_master crm where crm.client_id is not null)
        '''

        # Other Donation Query
        donation_query = '''
        select sum(don.amount) AS donation_amount
        from marketing.donation don,
               marketing.donor r,
               marketing.donation_types dt,
               billing.payment_mode pm,
               finance.gl_coa c
        where don.donor_id = r.donor_id
        and don.donation_type_id = dt.donation_type_id
        and don.donation_group_id = dt.donation_group_id
        and don.mode_id = pm.payment_mode_id
        and don.coa_code_cr = c.coa_code(+)
        and don.receipt_location_id='101'
        and don.trans_date >= sysdate-30
        '''

        # Other Donation Query
        total_debtor_billing = '''
        Select
        sum(fim.net_receivable)
        BILLING
        From
        Billing.Final_Invoice_Master
        fim
        Where
        fim.final_invoice_type
        IN('R', 'H')
        and fim.final_invoice_date >= sysdate - 30
'''
        pharmacy_consumption ='''
        select
        sum(std.moving_average_cost * std.transfered_qty) + sum(std.moving_average_cost * std.cancel_qty)
        Total_Con
        from mms.store_transfer_master stm, item.store
        fs, item.store
        ts, hrd.vu_information
        i,
        mms.store_transfer_detail
        std
    where
    stm.trans_no = std.trans_no
    and stm.from_store_id = fs.store_id
    and stm.to_store_id = ts.store_id
    and UPPER(fs.description)
    like
    '%FMH IN HOUSE%'
    and stm.approved_date >= '01-JAN-2025'
    and stm.approved_date < '01-FEB-2025'
    and stm.delivered_by = i.MRNO
    and std.transaction_type_id = '026'
    order
    by stm.approved_date
    '''

        # Execute queries
        cursor.execute(debtor_query)
        total_receivable = cursor.fetchone()[0] or 0

        cursor.execute(consumption_query)
        consumption_row = cursor.fetchone()
        consumption_qty = consumption_row[0] or 0
        consumption_value = consumption_row[1] or 0

        cursor.execute(receipts_query)
        gross_amount = cursor.fetchone()[0] or 0

        cursor.execute(donation_query)
        donation_amount = cursor.fetchone()[0] or 0

        cursor.execute(total_debtor_billing)
        total_debtor_billing = cursor.fetchone()[0] or 0

        cursor.execute(pharmacy_consumption)
        pharmacy_consumption = cursor.fetchone()[0] or 0

        result = {
            "total_receivable": float(total_receivable),
            "consumption": {
                "quantity": float(consumption_qty),
                "value": float(consumption_value)
            },
            "client_receipts": float(gross_amount),
            "donations": float(donation_amount),
"total_debtor_billing": float(total_debtor_billing),
            "pharmacy_consumption": float(pharmacy_consumption)

  }

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
