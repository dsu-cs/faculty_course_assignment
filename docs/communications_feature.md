# Communications Feature

**Manager:** Muhammad Bhutta  
**Team:** Lindsey Crow, Tyler Hardy  
**Status:** In Development

## Overview
Handles bidirectional communication between Excel workbook and Solver server.

## Components

### Server Side (Python)
- Flask web server
- Receives CSV data from Excel
- Invokes solver
- Returns results

### Client Side (VBA)
- Excel button triggers solver
- Packages data into JSON/CSV
- Sends to server
- Displays results

## Current Status
- [x] Project structure created
- [x] Requirements.txt added
- [ ] Server stub implementation
- [ ] VBA client stub
- [ ] Integration testing

## Next Steps
1. Implement Flask server stub
2. Create VBA client code
3. Test local integration
4. Deploy to Linux server