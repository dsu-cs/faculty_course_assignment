Communications Feature

Manager: Muhammad Bhutta
Developers: Lindsey Crow, Tyler Hardy
Status: COMPLETE - Ready for Integration

Overview

Handles bidirectional communication between Excel workbook and Solver server.

Components Delivered

Server Side (Python Flask)

- Flask REST API server with 3 endpoints (/, /health, /solve)
- Integration with Anto's OR-Tools solver
- JSON request handling and CSV conversion
- Comprehensive error handling and logging
- All 7 tests passing
- Complete API documentation (API_SPEC.md)

Client Side (Excel VBA)

- Three VBA modules ready to import
  - SolverAPI.bas - API communication
  - ExcelDataHelper.bas - Excel data reader
  - MainController.bas - Workflow orchestrator
- Complete Excel workbook with sample data
- Python automation script (build_workbook.py)
- Installation and usage documentation

Integration

- End-to-end workflow implemented
- User fills Excel sheets, clicks button, results appear
- Tested with sample data
- Ready for production deployment

Status

Completed:
- Flask server implementation (MERGED TO MAIN)
- Solver integration
- API specification
- VBA client suite
- Excel workbook
- Sample data
- Documentation
- All tests passing

In Progress:
- Tyler Hardy: nginx deployment configuration (assigned, not started)
- Lindsey Crow: VBA customization for DSU production data (not started)

Files Location


- solver_server/communications/vba_integration/MainController.bas
- solver_server/communications/vba_integration/FacultyCourseAssignment.xlsx

Pull Requests

- PR 9: Communications Server (MERGED)
- VBA integration work ready for next PR

Next Steps

1. Lindsey imports VBA modules into production workbook
2. Tyler completes nginx reverse proxy setup
3. Team conducts end-to-end testing with real DSU data
4. Deploy to Linux serverCommunications-Setup Branch:
- solver_server/communications/vba_integration/SolverAPI.bas
- solver_server/communications/vba_integration/ExcelDataHelper.bas
Main Branch:
- solver_server/communications/server.py
- solver_server/communications/tests/test_server.py

