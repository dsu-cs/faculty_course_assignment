"""
Communications Server - Listens for Excel workbook requests
Author: Muhammad Bhutta
Feature: Communications to/from Server
Team: Lindsey Crow, Tyler Hardy
Updated: April 1, 2026 - Added validation endpoint
"""
from flask import Flask, request, jsonify
import logging
from datetime import datetime
import sys
import os
import subprocess

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Solver paths
SOLVER_DIR = '/app/Solver'
SOLVER_SCRIPT = os.path.join(SOLVER_DIR, 'src/faculty_scheduling.py')
SCHEDULE_OUTPUT = os.path.join(SOLVER_DIR, 'schedule.csv')

@app.route('/', methods=['GET'])
def home():
    """Home endpoint - shows server is running"""
    return jsonify({
        "service": "Faculty Course Assignment Solver Server",
        "version": "0.3.0",
        "author": "Muhammad Bhutta",
        "status": "running",
        "solver_integrated": True,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy",
        "service": "solver-server",
        "solver_integrated": True
    })

@app.route('/solve', methods=['POST'])
def solve():
    """Main endpoint - receives CSVs, calls solver, returns results"""
    try:
        data = request.get_json(force=True, silent=True)
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        run_id = data.get('run_id', 'run_' + datetime.now().strftime("%Y%m%d_%H%M%S"))
        logger.info(f"Processing solve request - run_id: {run_id}")
        
        # Save CSV files to Solver directory
        required_files = ['sections_csv', 'time_blocks_csv', 'preferences_csv']
        missing = [f for f in required_files if f not in data]
        
        if missing:
            return jsonify({
                "status": "error",
                "message": f"Missing required CSV data: {', '.join(missing)}"
            }), 400
        
        # Write CSV files
        try:
            with open(os.path.join(SOLVER_DIR, 'sections.csv'), 'w') as f:
                f.write(data['sections_csv'])
            
            with open(os.path.join(SOLVER_DIR, 'time_blocks.csv'), 'w') as f:
                f.write(data['time_blocks_csv'])
            
            with open(os.path.join(SOLVER_DIR, 'preferences.csv'), 'w') as f:
                f.write(data['preferences_csv'])
            
            # Workload is optional
            if 'workload_csv' in data and data['workload_csv']:
                with open(os.path.join(SOLVER_DIR, 'workload.csv'), 'w') as f:
                    f.write(data['workload_csv'])
            
            logger.info("CSV files saved to Solver directory")
        
        except Exception as e:
            logger.error(f"Failed to save CSV files: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to save CSV files: {str(e)}"
            }), 500
        
        # Call Anto's solver
        try:
            logger.info("Calling solver...")
            result = subprocess.run(
                ['python3', SOLVER_SCRIPT],
                cwd=SOLVER_DIR,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Solver failed: {result.stderr}")
                return jsonify({
                    "status": "error",
                    "message": "Solver execution failed",
                    "details": result.stderr
                }), 500
            
            logger.info("Solver completed successfully")
        
        except subprocess.TimeoutExpired:
            logger.error("Solver timeout")
            return jsonify({
                "status": "error",
                "message": "Solver timeout (>2 minutes)"
            }), 500
        
        except Exception as e:
            logger.error(f"Solver error: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Solver error: {str(e)}"
            }), 500
        
        # Read the output schedule.csv
        try:
            if not os.path.exists(SCHEDULE_OUTPUT):
                return jsonify({
                    "status": "error",
                    "message": "Solver did not produce output file"
                }), 500
            
            with open(SCHEDULE_OUTPUT, 'r') as f:
                schedule_data = f.read()
            
            logger.info(f"Schedule returned - run_id: {run_id}")
            
            return jsonify({
                "status": "success",
                "run_id": run_id,
                "schedule_csv": schedule_data,
                "timestamp": datetime.now().isoformat()
            }), 200
        
        except Exception as e:
            logger.error(f"Failed to read output: {str(e)}")
            return jsonify({
                "status": "error",
                "message": f"Failed to read solver output: {str(e)}"
            }), 500
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/validate', methods=['POST'])
def validate():
    """Validation endpoint - checks for constraint violations before solver runs"""
    try:
        # Get JSON data from request
        data = request.get_json(force=True, silent=True)
        
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400
        
        if not data:
            return jsonify({"status": "warning", "message": "Empty request"}), 200
        
        # Extract CSV data (same as /solve)
        sections_csv = data.get('sections_csv', '')
        time_blocks_csv = data.get('time_blocks_csv', '')
        preferences_csv = data.get('preferences_csv', '')
        workload_csv = data.get('workload_csv', '')
        
        logger.info("Processing validation request")
        
        # TODO: Add validation logic in next step
        # For now, return empty violations (placeholder)
        violations = []
        
        # Return detailed response
        return jsonify({
            "status": "success",
            "has_violations": len(violations) > 0,
            "violation_count": len(violations),
            "violations": violations,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Validation error: {str(e)}", exc_info=True)
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def start_server(host='0.0.0.0', port=5000, debug=True):
    """Start the Flask server"""
    logger.info("=" * 60)
    logger.info("Faculty Course Assignment Solver Server")
    logger.info(f"Author: Muhammad Bhutta")
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Solver integrated: True")
    logger.info("=" * 60)
    app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    start_server()