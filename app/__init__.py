from flask import Flask
from flask_cors import CORS
import oracledb
from app.routes.client_receipt_adjustment import cra_bp
from app.routes.ssp_refer_letter import ssp_bp
from app.routes.debtor_aging_master import dam_bp
from app.routes.trail_balance import tb_bp
from app.routes.general_ledger import gl_bp  # Import the gl blueprint
from app.routes.user import user_bp  # Import the gl blueprint
from app.routes.coa_codes import codes_bp  # Import the gl blueprint
from app.routes.debtor_aging_zero import daz_bp

def create_app():
    app = Flask(__name__)
    
    # Configure CORS with specific options
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    oracledb.init_oracle_client()

    # Register Blueprints
    app.register_blueprint(cra_bp)
    app.register_blueprint(ssp_bp)
    app.register_blueprint(dam_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(tb_bp)
    app.register_blueprint(codes_bp)
    app.register_blueprint(gl_bp)  # Register the gl blueprint
    app.register_blueprint(daz_bp)
    return app