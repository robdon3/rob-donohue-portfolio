/**
 * Reference pattern from a purpose-built Sheets workbook.
 *
 * Real Apps Script lives in the private spreadsheet.
 * This file documents the rules for the public demo (Python journal module
 * implements the same behavior).
 *
 * Rules:
 *  1. Read today's control-surface snapshot (date + key totals).
 *  2. Scan Journal column A only for last used row / same-day match
 *     (other columns may hold formulas — ignore them for "last row").
 *  3. Same calendar day → overwrite that row.
 *  4. New day → append after the last real date in column A.
 *
 * Why: re-run safe, methodical, one day one truth row.
 */

function copyDataToJournal() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var financialSheet = ss.getSheetByName("Financial Sheet");
  var journalSheet = ss.getSheetByName("Journal");

  // Get today's date from B25 and normalize
  var today = new Date(financialSheet.getRange("B25").getValue());
  today.setHours(0, 0, 0, 0);

  // Get data to record from B25:E25
  var dataValues = financialSheet.getRange("B25:E25").getValues();

  // Scan Column A only to determine last used row (ignore other columns with formulas)
  var columnA = journalSheet.getRange("A:A").getValues();
  var actualLastRow = 0;
  var foundRow = -1;

  for (var i = 0; i < columnA.length; i++) {
    var cell = columnA[i][0];
    if (cell !== "" && cell instanceof Date) {
      var cellDate = new Date(cell);
      cellDate.setHours(0, 0, 0, 0);
      actualLastRow = i + 1;

      if (cellDate.getTime() === today.getTime()) {
        foundRow = i + 1;
        break;
      }
    }
  }

  if (foundRow > 0) {
    // Overwrite existing row
    journalSheet.getRange(foundRow, 1, 1, dataValues[0].length).setValues(dataValues);
  } else {
    // Append new row at end of true column A data
    journalSheet.getRange(actualLastRow + 1, 1, 1, dataValues[0].length).setValues(dataValues);
  }
}
