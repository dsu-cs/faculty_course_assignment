"""
Communications Server - Listens for Excel workbook requests
Author: Muhammad Bhutta
Feature: Communications to/from Server
Team: Lindsey Crow, Tyler Hardy
"""

from flask import Flask, request, jsonify
import logging
from datetime import datetime
import sys
import os
import tempfile

# Add Solver directory to path
solver_path = os.path.join(os.path.dirname(__file__), '../../Solver/src')
sys.path.insert(0, solver_path)

try:
    from faculty_scheduling import load_all, build_csp, run_solver, validate
    from ortools.sat.python import cp_model
    SOLVER_AVAILABLE = True
except ImportError as e:
    SOLVER_AVAILABLE = False
    IMPORT_ERROR = str(e)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/', methods=['GET'])
def home():
    """Home endpoint - shows server is running"""
    return jsonify({
        "service": "Faculty Course Assignment Solver Server",
        "version": "0.2.0",
        "author": "Muhammad Bhutta",
        "status": "running",
        "solver_available": SOLVER_AVAILABLE,
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy",
        "service": "solver-server",
        "solver_available": SOLVER_AVAILABLE
    })


@app.route('/solve', methods=['POST'])
def solve():
    """Main endpoint - integrates with Anto's solver"""
    
    if not SOLVER_AVAILABLE:
        logger.error("Solver not available")
        return jsonify({
            "status": "error",
            "message": "Solver module not available"
        }), 500

    try:
        data = request.get_json(force=True, silent=True)

        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON"}), 400

        if not data:
            return jsonify({"status": "warning", "message": "Empty request"}), 200

        run_id = data.get('run_id', 'run_' + datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        logger.info(f"Processing solve request - run_id: {run_id}")

        # For MVP: Return stub response
        # TODO: Integrate full solver when CSV format is finalized
        return jsonify({
            "status": "success",
            "run_id": run_id,
            "message": "Solver integration ready - awaiting CSV format specification",
            "solver_available": True,
            "timestamp": datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
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
    logger.info(f"Solver available: {SOLVER_AVAILABLE}")
    logger.info("=" * 60)
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    start_server()
