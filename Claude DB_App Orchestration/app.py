from flask import Flask, render_template, request, jsonify, redirect, url_for
from models import db, Mason, CementUtilization, SteelCement, SandGravelBricks, RMC, Electrical, Plumbing, Grill, UPVC, Painting, Windows, Carpenter, Others, TotalCost, DadOthers, VPP, Expansion
import os
import logging
from datetime import datetime
import traceback
from sqlalchemy import text, Column, String, Integer, Float, Text, Date, DateTime, Boolean, inspect, MetaData
from sqlalchemy.ext.automap import automap_base
from dateutil import parser as date_parser
# from transaction_parsing_rules import TransactionParsingRules
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging based on environment
log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper())
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 
    f"postgresql://{os.environ.get('POSTGRES_USER', 'postgres')}:"
    f"{os.environ.get('POSTGRES_PASSWORD', 'postgres')}@"
    f"{os.environ.get('POSTGRES_HOST', 'db')}:"
    f"{os.environ.get('POSTGRES_PORT', '5432')}/"
    f"{os.environ.get('POSTGRES_DB', 'construction')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

# Flask configuration from environment
if os.environ.get('FLASK_ENV') == 'production':
    app.config['DEBUG'] = False
else:
    app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'true').lower() in ('true', '1', 'yes')

db.init_app(app)

# Table name to model mapping
TABLE_MODELS = {
    'mason': Mason,
    'cement_utilization': CementUtilization,
    'steel_cement': SteelCement,
    'sand_gravel_bricks': SandGravelBricks,
    'rmc': RMC,
    'electrical': Electrical,
    'plumbing': Plumbing,
    'grill': Grill,
    'upvc': UPVC,
    'painting': Painting,
    'windows': Windows,
    'carpenter': Carpenter,
    'others': Others,
    'total_cost': TotalCost,
    'dad_others': DadOthers,
    'vpp': VPP,
    'expansion': Expansion,
}

def safe_strip(value):
    """Safely strip a value that might be None"""
    if value is None:
        return ''
    return str(value).strip()

def get_actual_table_columns(table_name):
    """Get actual columns from the database table (not just the SQLAlchemy model)"""
    try:
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)
        return [col['name'] for col in columns]
    except Exception as e:
        logger.error(f"Error getting actual table columns for {table_name}: {e}")
        return []

def get_table_schema_info(table_name):
    """Get detailed schema information for a table"""
    try:
        inspector = inspect(db.engine)
        columns = inspector.get_columns(table_name)
        
        schema_info = []
        for col in columns:
            schema_info.append({
                'name': col['name'],
                'type': str(col['type']),
                'nullable': col['nullable'],
                'default': col['default'],
                'primary_key': col.get('primary_key', False)
            })
        
        return schema_info
    except Exception as e:
        logger.error(f"Error getting schema info for {table_name}: {e}")
        return []

def refresh_sqlalchemy_metadata():
    """Force SQLAlchemy to refresh its metadata cache"""
    try:
        # Clear the metadata cache
        db.metadata.clear()
        # Reflect the current database state
        db.metadata.reflect(bind=db.engine)
        logger.info("SQLAlchemy metadata refreshed")
        return True
    except Exception as e:
        logger.error(f"Error refreshing metadata: {e}")
        return False

def sync_model_with_database(table_name):
    """Dynamically update model to match database schema"""
    try:
        logger.info(f"Syncing model for table: {table_name}")
        
        # Get current database columns
        inspector = inspect(db.engine)
        db_columns = inspector.get_columns(table_name)
        
        # Get current model
        Model = TABLE_MODELS.get(table_name)
        if not Model:
            logger.error(f"No model found for table: {table_name}")
            return False
            
        # Get model columns
        model_columns = {col.name: col for col in Model.__table__.columns}
        
        # Check for missing columns in model
        missing_columns = []
        for db_col in db_columns:
            col_name = db_col['name']
            if col_name not in model_columns:
                missing_columns.append(db_col)
                
        if missing_columns:
            logger.info(f"Found {len(missing_columns)} missing columns in model: {[col['name'] for col in missing_columns]}")
            
            # Create new columns dynamically
            for db_col in missing_columns:
                col_name = db_col['name']
                col_type = db_col['type']
                
                # Map SQL types to SQLAlchemy types
                if 'integer' in str(col_type).lower():
                    sa_type = Integer
                elif 'double precision' in str(col_type).lower() or 'float' in str(col_type).lower():
                    sa_type = Float
                elif 'character varying' in str(col_type).lower():
                    sa_type = String(255)
                elif 'text' in str(col_type).lower():
                    sa_type = Text
                elif 'date' in str(col_type).lower() and 'timestamp' not in str(col_type).lower():
                    sa_type = Date
                elif 'timestamp' in str(col_type).lower():
                    sa_type = DateTime
                elif 'boolean' in str(col_type).lower():
                    sa_type = Boolean
                else:
                    sa_type = String(255)  # Default fallback
                
                # Add column to model's table
                new_column = Column(col_name, sa_type, nullable=db_col['nullable'])
                setattr(Model, col_name, new_column)
                Model.__table__.append_column(new_column)
                
                logger.info(f"Added column '{col_name}' to {Model.__name__} model")
            
            # Refresh metadata after changes
            refresh_sqlalchemy_metadata()
            
        logger.info(f"Model sync completed for {table_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error syncing model for {table_name}: {traceback.format_exc()}")
        return False

def ensure_all_models_synced():
    """Ensure all models are synced with database schema"""
    try:
        logger.info("Starting full model synchronization")
        for table_name in TABLE_MODELS.keys():
            sync_model_with_database(table_name)
        logger.info("Full model synchronization completed")
        return True
    except Exception as e:
        logger.error(f"Error in full model sync: {e}")
        return False

def get_sql_type_for_column_type(column_type, default_value=None):
    """Convert frontend column type to SQL type"""
    type_mapping = {
        'text': 'VARCHAR(255)',
        'longtext': 'TEXT',
        'number': 'INTEGER',
        'decimal': 'FLOAT',
        'date': 'DATE',
        'datetime': 'TIMESTAMP',
        'boolean': 'BOOLEAN'
    }
    
    sql_type = type_mapping.get(column_type, 'VARCHAR(255)')
    
    # Add default value if provided and not empty
    if default_value and default_value.strip():
        if column_type in ['text', 'longtext']:
            # Escape single quotes in default value
            escaped_value = default_value.replace("'", "''")
            sql_type += f" DEFAULT '{escaped_value}'"
        elif column_type in ['number', 'decimal']:
            try:
                float(default_value)  # Validate numeric
                sql_type += f" DEFAULT {default_value}"
            except ValueError:
                logger.warning(f"Invalid numeric default value: {default_value}")
        elif column_type == 'boolean':
            if default_value.lower() in ['true', '1', 'yes', 'on']:
                sql_type += " DEFAULT TRUE"
            else:
                sql_type += " DEFAULT FALSE"
    
    return sql_type

def perform_calculations(row_data, table_name):
    """Perform automatic calculations based on table type"""
    if table_name == 'steel_cement':
        # Calculate bags_amount = bags * perbagprice
        bags = safe_float_conversion(row_data.get('bags'))
        perbagprice = safe_float_conversion(row_data.get('perbagprice'))
        if bags and perbagprice:
            row_data['bags_amount'] = bags * perbagprice
        
        # Calculate total bill = sum of all amounts
        amounts = []
        amount_fields = ['bags_amount', 'mm20_amount', 'mm16_amount', 'mm12_amount', 'mm10_amount', 'mm8_amount']
        for field in amount_fields:
            amount = safe_float_conversion(row_data.get(field))
            if amount:
                amounts.append(amount)
        
        if amounts:
            row_data['bill'] = sum(amounts)
    
    elif table_name in ['electrical', 'plumbing', 'sand_gravel_bricks']:
        # Calculate balance = bill - paid
        bill = safe_float_conversion(row_data.get('bill'))
        paid = safe_float_conversion(row_data.get('paid'))
        if bill is not None and paid is not None:
            row_data['balance'] = bill - paid
    
    return row_data

def safe_float_conversion(value):
    """Safely convert value to float"""
    if value is None or value == '':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_convert_value(value, column_name, model_class):
    """Safely convert values based on column type"""
    if value in (None, '', 'null', 'undefined'):
        return None
    
    # Get column type from model
    column = getattr(model_class.__table__.columns, column_name, None)
    if column is None:
        return value
    
    column_type = str(column.type)
    
    try:
        if 'INTEGER' in column_type.upper():
            return int(float(value)) if value not in ('', None) else None
        elif 'FLOAT' in column_type.upper() or 'REAL' in column_type.upper():
            return float(value) if value not in ('', None) else None
        elif 'DATE' in column_type.upper() and 'DATETIME' not in column_type.upper():
            if isinstance(value, str) and value.strip():
                return datetime.strptime(value.split()[0], '%Y-%m-%d').date()
            return None
        elif 'DATETIME' in column_type.upper() or 'TIMESTAMP' in column_type.upper():
            if isinstance(value, str) and value.strip():
                try:
                    return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        return datetime.strptime(value, '%Y-%m-%d %H:%M:%S.%f')
                    except ValueError:
                        date_part = datetime.strptime(value.split()[0], '%Y-%m-%d').date()
                        return datetime.combine(date_part, datetime.now().time())
            return None
        else:
            return str(value) if value is not None else None
    except (ValueError, TypeError) as e:
        logger.warning(f"Could not convert value '{value}' for column '{column_name}': {e}")
        return None

def normalize_value_for_comparison(value):
    """Normalize values for comparison (handle None, empty strings, etc.)"""
    if value is None or value == '' or value == 'null' or value == 'undefined':
        return None
    if isinstance(value, str):
        return value.strip()
    return value

def row_has_changed(new_row_data, existing_row, columns):
    """Check if a row has actually changed by comparing field values"""
    if not existing_row:
        return True  # New row, definitely changed
    
    for col in columns:
        if col in ('id', 'timestamp'):  # Skip ID and timestamp for comparison
            continue
            
        new_value = normalize_value_for_comparison(new_row_data.get(col))
        
        # Get existing value and convert it to string for comparison (like from frontend)
        existing_value = getattr(existing_row, col, None)
        if existing_value is None:
            existing_value = None
        elif isinstance(existing_value, datetime):
            existing_value = existing_value.strftime('%Y-%m-%d %H:%M:%S')
        elif hasattr(existing_value, 'strftime'):  # date objects
            existing_value = existing_value.strftime('%Y-%m-%d')
        
        existing_value = normalize_value_for_comparison(existing_value)
        
        # Compare normalized values
        if str(new_value) != str(existing_value):
            logger.debug(f"Column '{col}' changed: '{existing_value}' -> '{new_value}'")
            return True
    
    return False

def parse_flexible_date(value):
    """Try to parse a date string in multiple common formats and return a date or datetime object."""
    if value in (None, '', 'null', 'undefined'):
        return None
    if isinstance(value, (datetime,  )):
        return value
    if isinstance(value, str):
        try:
            # Try dateutil parser first (handles most formats)
            dt = date_parser.parse(value, dayfirst=True, fuzzy=True)
            return dt
        except Exception:
            pass
        # Try some common manual formats
        for fmt in ["%d-%b", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%d-%b-%Y", "%b-%d-%Y", "%d %b %Y", "%d %B %Y"]:
            try:
                dt = datetime.strptime(value, fmt)
                return dt
            except Exception:
                continue
    return value

@app.route('/')
def index():
    """Enhanced dashboard with statistics"""
    try:
        # Get table counts
        table_counts = {}
        total_records = 0
        
        for table_name, model in TABLE_MODELS.items():
            try:
                # Simple direct count using raw SQL
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {model.__tablename__}"))
                count = result.scalar() or 0
                table_counts[table_name] = count
                total_records += count
            except Exception as e:
                # If table doesn't exist or has issues, set to 0
                table_counts[table_name] = 0
        
        # Calculate some basic statistics
        total_expense = 0
        pending_amount = 0
        
        try:
            # Get total from TotalCost table if available
            total_cost_records = TotalCost.query.all()
            for record in total_cost_records:
                if record.bill:
                    total_expense += record.bill
                if record.balance:
                    pending_amount += record.balance
        except Exception as e:
            logger.warning(f"Could not calculate expenses: {e}")
        
        # Format amounts for display
        total_expense_formatted = f"{total_expense/100000:.1f}L" if total_expense > 100000 else f"{total_expense/1000:.0f}K"
        pending_amount_formatted = f"{pending_amount/100000:.1f}L" if pending_amount > 100000 else f"{pending_amount/1000:.0f}K"
        
        return render_template('dashboard.html', 
                             tables=list(TABLE_MODELS.keys()),
                             table_counts=table_counts,
                             total_records=total_records,
                             total_expense=total_expense_formatted,
                             pending_amount=pending_amount_formatted)
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        # Fallback to basic index
        return render_template('index.html', tables=list(TABLE_MODELS.keys()))

@app.route('/<table>')
def table_grid(table):
    try:
        Model = TABLE_MODELS.get(table)
        if not Model:
            return f"Table '{table}' not found.", 404
        
        # Force refresh metadata to pick up any new columns
        refresh_sqlalchemy_metadata()
        
        # Sync model with database schema to ensure consistency
        sync_model_with_database(table)
        
        # Get actual columns from database, not just model
        actual_columns = get_actual_table_columns(Model.__tablename__)
        model_columns = [c.name for c in Model.__table__.columns]
        
        logger.info(f"Model columns for {table}: {model_columns}")
        logger.info(f"Actual DB columns for {table}: {actual_columns}")
        
        # Use actual columns if available, fallback to model columns
        columns = actual_columns if actual_columns else model_columns
        
        # Get data using raw SQL to handle dynamic columns
        data = []
        if actual_columns:
            try:
                # Build column list for SELECT, handling reserved keywords
                column_list = []
                for col in actual_columns:
                    if col in ['for', 'order', 'group']:  # PostgreSQL reserved words
                        column_list.append(f'"{col}"')
                    else:
                        column_list.append(col)
                
                sql = f"SELECT {', '.join(column_list)} FROM {Model.__tablename__} ORDER BY id"
                result = db.session.execute(text(sql))
                rows = result.fetchall()
                
                for row in rows:
                    row_data = {}
                    for i, col in enumerate(actual_columns):
                        try:
                            value = row[i]
                            # Convert datetime and date objects to strings for JSON serialization
                            if isinstance(value, datetime):
                                row_data[col] = value.strftime('%Y-%m-%d %H:%M:%S')
                            elif hasattr(value, 'strftime'):  # date objects
                                row_data[col] = value.strftime('%Y-%m-%d')
                            else:
                                row_data[col] = value
                        except (IndexError, AttributeError) as e:
                            logger.warning(f"Error accessing column {col} at index {i}: {e}")
                            row_data[col] = None
                    data.append(row_data)
                    
            except Exception as e:
                logger.error(f"Error fetching data with raw SQL: {e}")
                logger.error(f"SQL was: {sql}")
                # Fallback to empty data if SQL fails
                data = []
        
        logger.info(f"Loaded {len(data)} rows for table {table} with {len(columns)} columns")
        
        # Try to use enhanced template first, fallback to original
        try:
            return render_template('table_grid_enhanced.html', columns=columns, data=data, table=table)
        except Exception as e:
            logger.warning(f"Enhanced template error: {e}, using original")
            return render_template('mason_grid.html', columns=columns, data=data, table=table)
    
    except Exception as e:
        logger.error(f"Error loading table {table}: {traceback.format_exc()}")
        return f"Error loading table: {str(e)}", 500

@app.route('/<table>/schema', methods=['GET'])
def get_table_schema(table):
    """Get detailed schema information for a table"""
    try:
        Model = TABLE_MODELS.get(table)
        if not Model:
            return jsonify({'success': False, 'message': f"Table '{table}' not found."}), 404
        
        table_name = Model.__tablename__
        schema_info = get_table_schema_info(table_name)
        model_columns = [c.name for c in Model.__table__.columns]
        actual_columns = [col['name'] for col in schema_info]
        
        return jsonify({
            'success': True,
            'table': table,
            'table_name': table_name,
            'model_columns': model_columns,
            'actual_columns': actual_columns,
            'schema_info': schema_info,
            'columns_match': set(model_columns) == set(actual_columns),
            'column_count': len(actual_columns)
        })
    
    except Exception as e:
        logger.error(f"Error getting schema for {table}: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/<table>/columns', methods=['GET'])
def get_table_columns(table):
    """Get actual columns for a table (for debugging)"""
    try:
        Model = TABLE_MODELS.get(table)
        if not Model:
            return jsonify({'success': False, 'message': f"Table '{table}' not found."}), 404
        
        model_columns = [c.name for c in Model.__table__.columns]
        actual_columns = get_actual_table_columns(Model.__tablename__)
        
        return jsonify({
            'success': True,
            'table': table,
            'model_columns': model_columns,
            'actual_columns': actual_columns,
            'columns_match': set(model_columns) == set(actual_columns),
            'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        logger.error(f"Error getting columns for {table}: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/<table>/refresh', methods=['POST'])
def refresh_table(table):
    """Force refresh the table metadata and reload"""
    try:
        Model = TABLE_MODELS.get(table)
        if not Model:
            return jsonify({'success': False, 'message': f"Table '{table}' not found."}), 404
        
        # Force refresh SQLAlchemy metadata
        success = refresh_sqlalchemy_metadata()
        
        # Sync model with database schema
        sync_success = sync_model_with_database(table)
        
        if success and sync_success:
            return jsonify({
                'success': True,
                'message': f'Table {table} metadata and model synced successfully. Page will reload to show latest schema.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to refresh metadata.'
            })
    
    except Exception as e:
        logger.error(f"Error refreshing table {table}: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/<table>/add-column', methods=['POST'])
def add_column(table):
    try:
        logger.info(f"Attempting to add column to table: {table}")
        Model = TABLE_MODELS.get(table)
        if not Model:
            logger.error(f"Table '{table}' not found in TABLE_MODELS")
            return jsonify({'success': False, 'message': f"Table '{table}' not found."}), 404
        request_data = request.get_json()
        if not request_data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data received'}), 400
        logger.debug(f"Received request data: {request_data}")
        column_name = safe_strip(request_data.get('column_name', ''))
        column_type = safe_strip(request_data.get('column_type', 'text'))
        default_value = safe_strip(request_data.get('default_value', ''))
        position = safe_strip(request_data.get('position', 'end'))
        after_column = request_data.get('after_column')
        logger.debug(f"Processed values - Name: '{column_name}', Type: '{column_type}', Default: '{default_value}', Position: '{position}'")
        if not column_name:
            return jsonify({'success': False, 'message': 'Column name is required'}), 400
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
            return jsonify({'success': False, 'message': 'Column name must start with a letter or underscore and contain only letters, numbers, and underscores'}), 400
        table_name = Model.__tablename__
        actual_columns = get_actual_table_columns(table_name)
        model_columns = [c.name for c in Model.__table__.columns]
        logger.info(f"Model columns: {model_columns}")
        logger.info(f"Actual DB columns: {actual_columns}")
        if column_name in actual_columns:
            return jsonify({'success': False, 'message': f'Column "{column_name}" already exists in the database table'}), 400
        if column_name in model_columns:
            return jsonify({'success': False, 'message': f'Column "{column_name}" already exists in the model'}), 400
        sql_type = get_sql_type_for_column_type(column_type, default_value if default_value else None)
        # Determine new column order
        if position == 'end' or not after_column:
            new_columns = actual_columns + [column_name]
        else:
            if position == 'before' and after_column in actual_columns:
                idx = actual_columns.index(after_column)
                new_columns = actual_columns[:idx] + [column_name] + actual_columns[idx:]
            elif position == 'after' and after_column in actual_columns:
                idx = actual_columns.index(after_column) + 1
                new_columns = actual_columns[:idx] + [column_name] + actual_columns[idx:]
            else:
                new_columns = actual_columns + [column_name]
        # Get column types for all columns
        inspector = inspect(db.engine)
        old_schema = inspector.get_columns(table_name)
        col_types = {col['name']: str(col['type']) for col in old_schema}
        col_nullable = {col['name']: col['nullable'] for col in old_schema}
        col_default = {col['name']: col['default'] for col in old_schema}
        # Add new column type
        col_types[column_name] = sql_type.split()[0]  # crude, but works for most
        col_nullable[column_name] = True
        col_default[column_name] = default_value if default_value else None
        # Build CREATE TABLE statement for new table
        new_table_name = f"{table_name}_new"
        col_defs = []
        for col in new_columns:
            col_def = f'"{col}" {col_types.get(col, "VARCHAR(255)")}'
            if not col_nullable.get(col, True):
                col_def += ' NOT NULL'
            if col_default.get(col) not in (None, '', 'None'):
                if 'CHAR' in col_types.get(col, '').upper() or 'TEXT' in col_types.get(col, '').upper():
                    col_def += f" DEFAULT '{col_default[col]}'"
                else:
                    col_def += f" DEFAULT {col_default[col]}"
            if col == 'id':
                col_def += ' PRIMARY KEY'
            col_defs.append(col_def)
        create_sql = f"CREATE TABLE {new_table_name} ({', '.join(col_defs)})"
        # Copy data from old table to new table (only columns that exist in both)
        copy_columns = [col for col in new_columns if col != column_name]
        quoted_cols = [f'"{col}"' for col in copy_columns]
        insert_sql = f"INSERT INTO {new_table_name} ({', '.join(quoted_cols)}) SELECT {', '.join(quoted_cols)} FROM {table_name}"
        # Drop old table and rename new table
        drop_sql = f"DROP TABLE {table_name} CASCADE"
        rename_sql = f"ALTER TABLE {new_table_name} RENAME TO {table_name}"
        # Execute all steps in a transaction
        try:
            db.session.execute(text(create_sql))
            db.session.execute(text(insert_sql))
            db.session.execute(text(drop_sql))
            db.session.execute(text(rename_sql))
            db.session.commit()
            refresh_sqlalchemy_metadata()
            
            # Sync model with database schema after adding column
            sync_model_with_database(table)
            
            logger.info(f"Successfully added column '{column_name}' to table '{table_name}' with reordering.")
            return jsonify({
                'success': True, 
                'message': f"Column '{column_name}' added successfully to {table.replace('_', ' ').title()} table in the correct position. Refreshing page to show new column..."
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during column addition with reordering: {traceback.format_exc()}")
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"General error in add_column: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

def normalize_value_for_comparison(value):
    """Normalize values for comparison to handle type differences and None/empty equivalences"""
    if value in (None, '', 'null', 'undefined', 'None'):
        return None
    
    # Handle date and datetime objects - convert to string for comparison
    if hasattr(value, 'strftime'):  # datetime.date or datetime.datetime
        if hasattr(value, 'time'):  # datetime.datetime
            return value.strftime('%Y-%m-%d %H:%M:%S')
        else:  # datetime.date
            return value.strftime('%Y-%m-%d')
    
    if isinstance(value, str):
        # Handle string representations of None/null
        stripped = value.strip()
        if stripped.lower() in ('none', 'null', ''):
            return None
        
        # Only convert to numbers if it looks like a pure number
        # Avoid converting dates, names, or other text that might contain numbers
        if stripped.replace('.', '').replace('-', '').replace('+', '').replace('e', '').replace('E', '').isdigit():
            try:
                if '.' in stripped:
                    return float(stripped)
                else:
                    return int(stripped)
            except (ValueError, TypeError):
                return stripped
        
        return stripped
    
    return value

@app.route('/<table>/save', methods=['POST'])
def table_save(table):
    try:
        logger.info(f"Attempting to save data for table: {table}")
        Model = TABLE_MODELS.get(table)
        if not Model:
            logger.error(f"Table '{table}' not found in TABLE_MODELS")
            return jsonify({'success': False, 'message': f"Table '{table}' not found."}), 404
        request_data = request.get_json()
        if not request_data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data received'}), 400
        rows = request_data.get('rows', [])
        logger.info(f"Received {len(rows)} rows to save")
        if not rows:
            logger.warning("No rows data in request")
            return jsonify({'success': False, 'message': 'No rows data provided'}), 400
        actual_columns = get_actual_table_columns(Model.__tablename__)
        columns = actual_columns if actual_columns else [c.name for c in Model.__table__.columns]
        logger.info(f"Table columns: {columns}")
        # Get column types for date/datetime detection
        inspector = inspect(db.engine)
        schema = inspector.get_columns(Model.__tablename__)
        col_types = {col['name']: str(col['type']).lower() for col in schema}
        existing_rows = {}
        try:
            if 'id' in columns:
                sql = f"SELECT * FROM {Model.__tablename__} ORDER BY id"
                result = db.session.execute(text(sql))
                for row in result:
                    row_dict = dict(row._mapping)
                    if 'id' in row_dict and row_dict['id'] is not None:
                        existing_rows[row_dict['id']] = row_dict
        except Exception as e:
            logger.warning(f"Could not load existing rows: {e}")
        logger.info(f"Found {len(existing_rows)} existing rows with IDs")
        try:
            delete_sql = f"DELETE FROM {Model.__tablename__}"
            db.session.execute(text(delete_sql))
            new_objects_count = 0
            changed_rows = 0
            preserved_rows = 0
            # Find the maximum existing ID to generate new IDs for rows without them
            max_existing_id = 0
            if existing_rows:
                max_existing_id = max(existing_rows.keys())
            
            next_new_id = max_existing_id + 1
            
            for i, row in enumerate(rows):
                # More lenient check - only skip completely empty rows (all values None/empty except id)
                meaningful_values = [v for k, v in row.items() if k not in ('id', 'timestamp') and v not in (None, '', 'null', 'undefined')]
                # Only skip if ALL values are empty AND there's no existing ID
                if not meaningful_values and not row.get('id'):
                    continue
                
                # Auto-generate ID for new rows that have meaningful data but no ID
                if not row.get('id') and meaningful_values:
                    row['id'] = next_new_id
                    next_new_id += 1
                    logger.debug(f"Auto-generated ID {row['id']} for new row {i}")
                
                # Perform automatic calculations before saving
                row = perform_calculations(row, table)
                insert_columns = []
                insert_values = []
                row_id = row.get('id')
                existing_row = existing_rows.get(row_id) if row_id else None
                
                # Proper change detection - compare current row with existing row
                has_changed = False
                if not existing_row:
                    has_changed = True  # New row
                else:
                    # Check if any non-timestamp column has changed
                    for col in columns:
                        if col in ('id', 'timestamp'):
                            continue
                        current_val = row.get(col)
                        existing_val = existing_row.get(col)
                        
                        # Normalize values for comparison
                        # Handle type conversions and None/empty equivalences
                        norm_current = normalize_value_for_comparison(current_val)
                        norm_existing = normalize_value_for_comparison(existing_val)
                        
                        logger.debug(f"Column '{col}' comparison: existing='{existing_val}'({type(existing_val)}) -> current='{current_val}'({type(current_val)})")
                        logger.debug(f"Column '{col}' normalized: existing='{norm_existing}' -> current='{norm_current}'")
                        
                        if norm_current != norm_existing:
                            logger.info(f"Row {row_id} column '{col}' CHANGED: '{norm_existing}' -> '{norm_current}'")
                            has_changed = True
                            break
                        else:
                            logger.debug(f"Column '{col}' unchanged")
                            
                # Log the final change detection result
                logger.info(f"Row {row_id} change detection result: has_changed={has_changed}")
                for col in columns:
                    raw_value = row.get(col)
                    
                    # Handle id column specially - include it if it exists in the row
                    if col == 'id':
                        if raw_value is not None:
                            insert_columns.append(col)
                            insert_values.append(raw_value)
                        continue
                    # Special handling for timestamp columns
                    if col == 'timestamp':
                        if has_changed:
                            final_value = datetime.utcnow()
                            if existing_row:
                                logger.debug(f"Row {i} changed - updating timestamp to current time")
                                changed_rows += 1
                            else:
                                logger.debug(f"Row {i} is new - setting current timestamp")
                        elif existing_row:
                            final_value = existing_row.get(col, datetime.utcnow())
                            logger.debug(f"Row {i} unchanged - preserving timestamp: {final_value}")
                            preserved_rows += 1
                        else:
                            final_value = datetime.utcnow()
                    else:
                        # Convert value appropriately
                        if raw_value in (None, '', 'null', 'undefined'):
                            final_value = None
                        else:
                            # Standardize date/datetime columns
                            if 'date' in col_types.get(col, '') or 'timestamp' in col_types.get(col, ''):
                                parsed = parse_flexible_date(raw_value)
                                # If column is just 'date', convert to .date()
                                if parsed and 'date' in col_types.get(col, '') and 'time' not in col_types.get(col, ''):
                                    try:
                                        final_value = parsed.date()
                                    except Exception:
                                        final_value = parsed
                                else:
                                    final_value = parsed
                            else:
                                final_value = raw_value
                    insert_columns.append(col)
                    insert_values.append(final_value)
                if insert_columns:
                    # Quote reserved keywords in column names
                    quoted_columns = []
                    for col in insert_columns:
                        if col in ['for', 'order', 'group']:  # PostgreSQL reserved words
                            quoted_columns.append(f'"{col}"')
                        else:
                            quoted_columns.append(col)
                    column_names = ', '.join(quoted_columns)
                    placeholders = ', '.join([':param' + str(j) for j in range(len(insert_values))])
                    sql = f"INSERT INTO {Model.__tablename__} ({column_names}) VALUES ({placeholders})"
                    params = {f'param{j}': val for j, val in enumerate(insert_values)}
                    try:
                        db.session.execute(text(sql), params)
                        new_objects_count += 1
                    except Exception as e:
                        logger.error(f"Error inserting row {i}: {e}")
                        logger.error(f"SQL: {sql}")
                        logger.error(f"Params: {params}")
                        continue
            db.session.commit()
            logger.info(f"Successfully saved {new_objects_count} rows to {table}")
            logger.info(f"Changed rows (updated timestamp): {changed_rows}")
            logger.info(f"Unchanged rows (preserved timestamp): {preserved_rows}")
            return jsonify({
                'success': True, 
                'message': f"{table.replace('_', ' ').title()} table updated successfully. Saved {new_objects_count} rows. {changed_rows} rows were modified and got new timestamps."
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during save: {traceback.format_exc()}")
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"General error in table_save: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Add a test endpoint to check database connectivity
@app.route('/test-db')
def test_db():
    try:
        # Try to query one of the tables
        mason_count = Mason.query.count()
        return jsonify({
            'success': True,
            'message': f'Database connection successful. Mason table has {mason_count} rows.',
            'database_url': app.config['SQLALCHEMY_DATABASE_URI']
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Database connection failed: {str(e)}',
            'error': traceback.format_exc()
        })

@app.route('/admin/sync-models', methods=['POST'])
def sync_all_models():
    """Manually sync all models with database schema"""
    try:
        ensure_all_models_synced()
        return jsonify({
            'success': True, 
            'message': 'All models have been synchronized with database schema'
        })
    except Exception as e:
        return jsonify({
            'success': False, 
            'message': f'Error syncing models: {str(e)}'
        }), 500

@app.route('/api/intelligent-parse', methods=['POST'])
def intelligent_parse_transactions():
    """
    Intelligent transaction parser endpoint
    Accepts natural language text and converts to structured database records
    """
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'message': 'No text provided for parsing'
            }), 400
        
        text = data['text']
        year = data.get('year', 2024)
        auto_insert = data.get('auto_insert', False)
        export_to_excel = data.get('export_to_excel', False)
        
        # Initialize parser
        parser = TransactionParsingRules()
        
        # Parse transactions
        transactions = parser.parse_transactions(text)
        db_records = parser.format_for_database(transactions)
        
        logger.info(f"Parsed {len(transactions)} transactions from text")
        
        results = {
            'success': True,
            'parsed_transactions': len(transactions),
            'tables_affected': list(db_records.keys()),
            'transactions': transactions,
            'db_records': db_records
        }
        
        # Auto-insert if requested
        if auto_insert:
            insertion_results = {}
            for table_name, records in db_records.items():
                try:
                    Model = TABLE_MODELS.get(table_name)
                    if not Model:
                        continue
                    
                    inserted_count = 0
                    for record in records:
                        # Build INSERT statement
                        columns = list(record.keys())
                        placeholders = [f':param{i}' for i in range(len(columns))]
                        sql = f"INSERT INTO {Model.__tablename__} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
                        params = {f'param{i}': val for i, val in enumerate(record.values())}
                        
                        db.session.execute(text(sql), params)
                        inserted_count += 1
                    
                    db.session.commit()
                    insertion_results[table_name] = inserted_count
                    logger.info(f"Inserted {inserted_count} records into {table_name}")
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error inserting into {table_name}: {e}")
                    insertion_results[table_name] = f"Error: {str(e)}"
            
            results['insertion_results'] = insertion_results
        
        # Export to Excel if requested
        if export_to_excel:
            try:
                excel_results = export_to_excel_mcp(db_records)
                results['excel_export'] = excel_results
            except Exception as e:
                logger.error(f"Excel export error: {e}")
                results['excel_export'] = f"Error: {str(e)}"
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error in intelligent parsing: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'Parsing error: {str(e)}'
        }), 500

def export_to_excel_mcp(db_records):
    """Export parsed transactions to Excel using MCP"""
    try:
        # Create a new workbook for the transactions
        workbook_name = f"transactions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # This would integrate with Excel MCP
        # For now, return structure that would be used
        excel_data = {}
        
        for table_name, records in db_records.items():
            if not records:
                continue
                
            # Convert records to Excel format
            headers = list(records[0].keys())
            rows = []
            
            for record in records:
                row = [str(record.get(col, '')) for col in headers]
                rows.append(row)
            
            excel_data[table_name] = {
                'headers': headers,
                'rows': rows,
                'total_records': len(rows)
            }
        
        return {
            'success': True,
            'workbook': workbook_name,
            'sheets': excel_data,
            'message': f'Prepared {len(excel_data)} sheets for Excel export'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'Excel export preparation failed: {str(e)}'
        }

# Add a route to delete a column from a table
@app.route('/<table>/delete-column', methods=['POST'])
def delete_column(table):
    try:
        logger.info(f"Attempting to delete column from table: {table}")
        Model = TABLE_MODELS.get(table)
        if not Model:
            logger.error(f"Table '{table}' not found in TABLE_MODELS")
            return jsonify({'success': False, 'message': f"Table '{table}' not found."}), 404
        request_data = request.get_json()
        if not request_data:
            logger.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data received'}), 400
        column_name = safe_strip(request_data.get('column_name', ''))
        if not column_name:
            return jsonify({'success': False, 'message': 'Column name is required'}), 400
        table_name = Model.__tablename__
        actual_columns = get_actual_table_columns(table_name)
        if column_name not in actual_columns:
            return jsonify({'success': False, 'message': f'Column "{column_name}" does not exist in the database table'}), 400
        # Build new column order (all except the one to delete)
        new_columns = [col for col in actual_columns if col != column_name]
        inspector = inspect(db.engine)
        old_schema = inspector.get_columns(table_name)
        col_types = {col['name']: str(col['type']) for col in old_schema}
        col_nullable = {col['name']: col['nullable'] for col in old_schema}
        col_default = {col['name']: col['default'] for col in old_schema}
        # Build CREATE TABLE statement for new table
        new_table_name = f"{table_name}_new"
        col_defs = []
        for col in new_columns:
            col_def = f'"{col}" {col_types.get(col, "VARCHAR(255)")}'
            if not col_nullable.get(col, True):
                col_def += ' NOT NULL'
            if col_default.get(col) not in (None, '', 'None'):
                if 'CHAR' in col_types.get(col, '').upper() or 'TEXT' in col_types.get(col, '').upper():
                    col_def += f" DEFAULT '{col_default[col]}'"
                else:
                    col_def += f" DEFAULT {col_default[col]}"
            if col == 'id':
                col_def += ' PRIMARY KEY'
            col_defs.append(col_def)
        create_sql = f"CREATE TABLE {new_table_name} ({', '.join(col_defs)})"
        # Copy data from old table to new table (only columns that exist in both)
        quoted_cols = [f'"{col}"' for col in new_columns]
        insert_sql = f"INSERT INTO {new_table_name} ({', '.join(quoted_cols)}) SELECT {', '.join(quoted_cols)} FROM {table_name}"
        # Drop old table and rename new table
        drop_sql = f"DROP TABLE {table_name} CASCADE"
        rename_sql = f"ALTER TABLE {new_table_name} RENAME TO {table_name}"
        try:
            db.session.execute(text(create_sql))
            db.session.execute(text(insert_sql))
            db.session.execute(text(drop_sql))
            db.session.execute(text(rename_sql))
            db.session.commit()
            refresh_sqlalchemy_metadata()
            
            # Sync model with database schema after deleting column
            sync_model_with_database(table)
            
            logger.info(f"Successfully deleted column '{column_name}' from table '{table_name}' with reordering.")
            return jsonify({
                'success': True,
                'message': f"Column '{column_name}' deleted successfully from {table.replace('_', ' ').title()} table. Refreshing page to show new schema..."
            })
        except Exception as e:
            db.session.rollback()
            logger.error(f"Database error during column deletion with reordering: {traceback.format_exc()}")
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
    except Exception as e:
        logger.error(f"General error in delete_column: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

# Add API endpoints for dashboard data
@app.route('/api/dashboard-stats')
def dashboard_stats():
    """API endpoint for dashboard statistics"""
    try:
        stats = {
            'total_tables': len(TABLE_MODELS),
            'total_records': 0,
            'table_counts': {},
            'recent_activity': []
        }
        
        for table_name, model in TABLE_MODELS.items():
            try:
                count = model.query.count()
                stats['table_counts'][table_name] = count
                stats['total_records'] += count
            except Exception as e:
                logger.warning(f"Could not get count for {table_name}: {e}")
                stats['table_counts'][table_name] = 0
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/expense-summary')
def expense_summary():
    """API endpoint for expense summary data"""
    try:
        summary = {
            'categories': [],
            'amounts': [],
            'total': 0
        }
        
        # Get data from major expense categories
        major_categories = ['steel_cement', 'mason', 'electrical', 'plumbing', 'others', 'sand_gravel_bricks']
        
        for category in major_categories:
            model = TABLE_MODELS.get(category)
            if model:
                try:
                    records = model.query.all()
                    total_amount = 0
                    for record in records:
                        if hasattr(record, 'bill') and record.bill:
                            total_amount += record.bill
                        elif hasattr(record, 'amount') and record.amount:
                            total_amount += record.amount
                    
                    summary['categories'].append(category.replace('_', ' ').title())
                    summary['amounts'].append(total_amount)
                    summary['total'] += total_amount
                except Exception as e:
                    logger.warning(f"Error calculating expenses for {category}: {e}")
        
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Total Cost Aggregation System

def get_table_data(model):
    """Get all records from a table model as list of dictionaries"""
    try:
        records = model.query.all()
        data = []
        for record in records:
            record_dict = {}
            for column in record.__table__.columns:
                value = getattr(record, column.name)
                if value is not None:
                    record_dict[column.name] = value
            data.append(record_dict)
        return data
    except Exception as e:
        logger.error(f"Error getting data from {model.__tablename__}: {e}")
        return []

@app.route('/api/aggregate-totals', methods=['POST'])
def aggregate_totals():
    """Collect totals from all tables and update Total Cost table"""
    try:
        aggregated_data = {}
        
        # 1. Mason table - get combined total (site + excess)
        try:
            mason_data = get_table_data(Mason)
            site_total = sum(float(row.get('site', 0) or 0) for row in mason_data)
            excess_total = sum(float(row.get('excess', 0) or 0) for row in mason_data)
            combined_total = site_total + excess_total
            aggregated_data['Mason'] = {
                'bill': combined_total,
                'paid': combined_total,
                'balance': 0
            }
            logger.info(f"Mason total: ₹{combined_total:,.2f} (Site: ₹{site_total:,.2f} + Excess: ₹{excess_total:,.2f})")
        except Exception as e:
            logger.error(f"Error collecting Mason data: {e}")
        
        # 2. Steel & Cement - get total paid
        try:
            steel_cement_data = get_table_data(SteelCement)
            total_paid = sum(float(row.get('paid', 0) or 0) for row in steel_cement_data)
            total_bill = sum(float(row.get('bill', 0) or 0) for row in steel_cement_data)
            balance = total_bill - total_paid
            aggregated_data['Steel & Cement'] = {
                'bill': total_bill,
                'paid': total_paid,
                'balance': balance
            }
            logger.info(f"Steel & Cement: Bill ₹{total_bill:,.2f}, Paid ₹{total_paid:,.2f}, Balance ₹{balance:,.2f}")
        except Exception as e:
            logger.error(f"Error collecting Steel & Cement data: {e}")
        
        # 3. Sand/Gravel/Bricks - get material summary
        try:
            sand_data = get_table_data(SandGravelBricks)
            material_totals = {}
            
            for row in sand_data:
                if row.get('paid') and row.get('type'):
                    paid_amount = float(row.get('paid', 0) or 0)
                    material_type = str(row.get('type', '')).strip()
                    
                    # Normalize type names
                    if material_type.lower() in ['sand']:
                        material_type = 'Sand'
                    elif material_type.lower() in ['msand', 'm-sand', 'm sand']:
                        material_type = 'Msand'
                    elif material_type.lower() in ['3/4']:
                        material_type = 'Gravel 3/4'
                    elif material_type.lower() in ['11/2', '1 1/2', '1½']:
                        material_type = 'Gravel 11/2'
                    elif material_type.lower() in ['bricks', 'brick']:
                        material_type = 'Bricks'
                    elif material_type.lower() in ['aac']:
                        material_type = 'AAC'
                    elif material_type.lower() in ['hb']:
                        material_type = 'HB'
                    
                    if material_type not in material_totals:
                        material_totals[material_type] = 0
                    material_totals[material_type] += paid_amount
            
            # Add each material type to aggregated data
            for material_type, total_paid in material_totals.items():
                aggregated_data[material_type] = {
                    'bill': total_paid,
                    'paid': total_paid,
                    'balance': 0
                }
                logger.info(f"{material_type}: ₹{total_paid:,.2f}")
                
        except Exception as e:
            logger.error(f"Error collecting Sand/Gravel/Bricks data: {e}")
        
        # 4. RMC - get total paid amounts
        try:
            rmc_data = get_table_data(Rmc)
            total_paid = sum(float(row.get('paid', 0) or 0) for row in rmc_data)
            total_bill = sum(float(row.get('bill', 0) or 0) for row in rmc_data)
            balance = total_bill - total_paid
            aggregated_data['RMC'] = {
                'bill': total_bill,
                'paid': total_paid,
                'balance': balance
            }
            logger.info(f"RMC: Bill ₹{total_bill:,.2f}, Paid ₹{total_paid:,.2f}, Balance ₹{balance:,.2f}")
        except Exception as e:
            logger.error(f"Error collecting RMC data: {e}")
        
        # 5. All other categories (Electrical, Plumbing, Grill, UPVC, Painting, Windows, Carpenter, Others)
        other_categories = {
            'Electrical': Electrical,
            'Plumbing': Plumbing,
            'Grill': Grill,
            'UPVC': UPVC,
            'Painting': Painting,
            'Windows': Windows,
            'Carpenter': Carpenter,
            'Others': Others
        }
        
        for category_name, model in other_categories.items():
            try:
                category_data = get_table_data(model)
                total_paid = sum(float(row.get('paid', 0) or 0) for row in category_data)
                total_bill = sum(float(row.get('bill', 0) or 0) for row in category_data)
                balance = total_bill - total_paid
                aggregated_data[category_name] = {
                    'bill': total_bill,
                    'paid': total_paid,
                    'balance': balance
                }
                logger.info(f"{category_name}: Bill ₹{total_bill:,.2f}, Paid ₹{total_paid:,.2f}, Balance ₹{balance:,.2f}")
            except Exception as e:
                logger.error(f"Error collecting {category_name} data: {e}")
        
        # 6. Update Total Cost table
        updated_count = 0
        for category_name, totals in aggregated_data.items():
            try:
                # Find existing record or create new one
                existing_record = TotalCost.query.filter_by(category=category_name).first()
                
                if existing_record:
                    # Update existing record
                    existing_record.bill = totals['bill']
                    existing_record.paid = totals['paid']
                    existing_record.balance = totals['balance']
                    updated_count += 1
                else:
                    # Create new record
                    new_record = TotalCost(
                        category=category_name,
                        bill=totals['bill'],
                        paid=totals['paid'],
                        balance=totals['balance']
                    )
                    db.session.add(new_record)
                    updated_count += 1
                    
            except Exception as e:
                logger.error(f"Error updating {category_name} in Total Cost: {e}")
        
        # Commit all changes
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully aggregated totals from all tables and updated {updated_count} categories in Total Cost',
            'aggregated_data': aggregated_data,
            'categories_updated': list(aggregated_data.keys())
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in aggregate_totals: {e}")
        return jsonify({
            'success': False,
            'message': f'Error aggregating totals: {str(e)}'
        }), 500

# Summary Dashboard Routes

@app.route('/sand_gravel_bricks/summary')
def sand_gravel_bricks_summary():
    """Sand, Gravel & Bricks summary dashboard"""
    return render_template('sand_gravel_bricks_summary.html',
                         table_name='sand_gravel_bricks',
                         category_name='Sand, Gravel & Bricks',
                         category_icon='fas fa-cube',
                         grouping_type='type')

@app.route('/electrical/summary')
def electrical_summary():
    """Electrical summary dashboard"""
    return render_template('electrical_summary.html',
                         table_name='electrical',
                         category_name='Electrical',
                         category_icon='fas fa-bolt',
                         grouping_type='type')

@app.route('/painting/summary')
def painting_summary():
    """Painting summary dashboard"""
    return render_template('painting_summary.html',
                         table_name='painting',
                         category_name='Painting',
                         category_icon='fas fa-paint-brush',
                         grouping_type='type')

@app.route('/rmc/summary')
def rmc_summary():
    """RMC summary dashboard"""
    return render_template('rmc_summary.html',
                         table_name='rmc',
                         category_name='RMC',
                         category_icon='fas fa-truck',
                         grouping_type='type')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)