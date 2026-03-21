"""
Communications Server - Listens for Excel workbook requests
Author: Muhammad Bhutta
Feature: Communications to/from Server
Team: Lindsey Crow, Tyler Hardy
"""

from flask import Flask, request, jsonify
import logging
from datetime import datetime

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
        "version": "0.1.0",
        "author": "Muhammad Bhutta",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    })


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy",
        "service": "solver-server"
    })


@app.route('/solve', methods=['POST'])
def solve():
    """
    Main endpoint for receiving Excel data and returning solver results
    
    This is a STUB implementation - will be fully implemented later
    
    Expected request format:
    {
        "sections": "csv_data_here",
        "faculty": "csv_data_here",
        "preferences": "csv_data_here"
    }
    
    Returns:
    {
        "status": "success|error",
        "message": "...",
        "violations": [],
        "warnings": [],
        "recommendations": []
    }
    """
    try:
        # Get data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data received"
            }), 400
        
        logger.info(f"Received solve request with {len(data)} keys")
        logger.info(f"Keys in request: {list(data.keys())}")
        
        # TODO: Validate data structure
        # TODO: Parse CSV data
        # TODO: Call CSV → CSP converter
        # TODO: Invoke solver
        # TODO: Parse results
        
        # For now, return a stub response
        response = {
            "status": "success",
            "message": "STUB: Server received your request successfully",
            "data_received": {
                "sections": "received" if "sections" in data else "missing",
                "faculty": "received" if "faculty" in data else "missing",
                "preferences": "received" if "preferences" in data else "missing"
            },
            "violations": [],
            "warnings": [
                {
                    "type": "info",
                    "message": "This is a stub implementation. Full solver coming soon!"
                }
            ],
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info("Returning stub response")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error processing solve request: {str(e)}", exc_info=True)
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
    logger.info(f"Debug mode: {debug}")
    logger.info("=" * 60)
    
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    start_server()