# CSV Integration VBA Modules

This folder contains the **current workbook-side VBA modules from integration work on 3/28/26**.

These files are the active modules for the current CSV-based solver integration path and are being kept separate from older legacy VBA to reduce confusion.

## Modules in this folder

### `ExcelDataHelper.bas`
Builds CSV strings from the workbook sheets.

Expected sheets:
- `Sections`
- `Time`
- `Preferences`

Current expected workbook structure:

#### Sections
- A = CRN
- B = Sub
- C = Num
- D = Seq
- E = Crd
- F = Desc
- G = Current Seats
- H = Max Seats
- I = Waitlist
- J = Faculty

#### Time
- A = CRN
- B = Sub
- C = Days
- D = Start Time
- E = End Time
- F = Room

#### Preferences
- Row 2 = `CRN, Faculty1, Faculty2, ...`
- Row 3+ = `CRN, score1, score2, ...`

Generated CSVs:
- `sections.csv`
- `time_blocks.csv`
- `preferences.csv`

Notes:
- `time_blocks.csv` exports time values in `HH:MM` format
- `preferences.csv` is currently matrix-style

---

### `AssignmentWriter.bas`
Applies returned solver assignments back into the workbook.

Expected response format:
```text
CRN,Assigned Faculty
70346,Erich Matthew Eischen
70377,Someone Else
```
## ActiveX Risk (Important)

The current SolverAPI implementation uses:

```text
MSXML2.XMLHTTP
```
