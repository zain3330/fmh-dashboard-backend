from flask import Blueprint, jsonify, request
from app.db import get_db_connection

from flask_cors import CORS

cb_bp = Blueprint("cb", __name__)
CORS(cb_bp)

@cb_bp.route('/cb', methods=['POST'])
def cb():
    data = request.get_json()
    year = data.get('year')
    clint = data.get('clint')  # Default to empty string if not provided
    # Validate required fields
    if not all([year]):
        return jsonify({"error": "Missing required fields"}), 400
    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        query = ''' 
        Select To_CHAR(td.trans_date,'MM-RRRR') Month, td.coa_code, gc.coa_description, 
               td.sub_ldgr_item_code Subsidiary_Code, gsl.sub_ldgr_item_desc Client, 
               (ob.open_dr-ob.open_cr) Opening_Balance,
               sum(td.dr_amount) Billing, sum(td.cr_amount) Receipt
        From Finance.Gl_Tran_Detail td, Finance.Gl_Coa gc, Finance.Gl_Sub_Ledgers gsl, 
             finance.gl_opening_balances ob, Finance.Gl_Financial_Year fy
        Where td.coa_code = '1113116004'
        and   trunc(td.trans_date) between fy.from_date and fy.to_date
        and   ob.year_code = :year
          AND LOWER(gsl.sub_ldgr_item_desc) LIKE :clint
        and   ob.year_code = fy.year_code
        and   td.coa_code = ob.coa_code
        and   td.sub_ldgr_item_code = ob.sub_ldgr_item_code
        and   td.ledger_type_code = ob.ledger_type_code
        and   td.coa_code = gc.coa_code
        and   td.ledger_type_code = gsl.ledger_type_code
        and   td.sub_ldgr_item_code = gsl.sub_ldgr_item_code
        Group by td.coa_code, gc.coa_description, td.ledger_type_code, td.sub_ldgr_item_code, 
                 gsl.sub_ldgr_item_desc, (ob.open_dr-ob.open_cr), To_CHAR(td.trans_date,'MM-RRRR')
        Order by td.sub_ldgr_item_code
        '''

        cursor.execute(query, {
            'year': year,
            'clint': f'%{clint.lower()}%' if clint else '%',

        })

        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        result = [{columns[i]: row[i] for i in range(len(columns))} for row in rows]

        if not result:
            print(f"No data found for year: {year}, client: {clint}")

        cursor.close()
        connection.close()

        return jsonify(result)

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return jsonify({"error": str(e)}), 500