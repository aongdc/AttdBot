"""
Classes defined for  Google Sheets workbook and
functions for reading and general modification of worksheets.
"""
import gspread
import gspread_formatting
from oauth2client.service_account import ServiceAccountCredentials


class Workbook:
    def __init__(self, cred_file, wb_name):
        self.cred_file = cred_file
        self.wb_name = wb_name
        self.creds = None
        self.client = None
        self.wb = self.connect()
        self.ws_all = None
        self.ws = None

    def connect(self):
        # Use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_name(self.cred_file, scope)
        self.client = gspread.authorize(self.creds)
        self.wb = self.client.open(self.wb_name)
        return self.wb

    def all_sheets(self):
        self.ws_all = self.wb.worksheets()
        return self.ws_all

    def add_sheet(self, title, rows, cols, idx=None):
        return self.wb.add_worksheet(title=title, rows=rows, cols=cols, idx=idx)

    def delete_sheet(self, sheet):
        self.ws = self.open_sheet(sheet)
        self.wb.del_worksheet(self.ws)

    def open_sheet(self, sheet):
        if type(sheet) is int:
            self.ws = self.wb.get_worksheet(sheet)
        else:
            self.ws = self.wb.worksheet(sheet)

        return self.ws

    def freeze(self, sheet, num_cols=0, num_rows=0):
        gspread_formatting.set_frozen(self.ws, cols=num_cols, rows=num_rows)


class Sheet(Workbook):
    def __init__(self, cred_file, wb_name, sheet):
        super().__init__(cred_file, wb_name)
        self.sheet = sheet

    def open(self):
        # Find a workbook by name and open the first sheet
        if type(self.sheet) is int:
            self.sheet = self.wb.get_worksheet(self.sheet)
        else:
            self.sheet = self.wb.worksheet(self.sheet)
        return self.sheet

    def delete(self):
        self.open()
        self.wb.del_worksheet(self.sheet)

    def freeze(self, num_cols=0, num_rows=0):
        gspread_formatting.set_frozen(self.sheet, cols=num_cols, rows=num_rows)


if __name__ == '__main__':
    from envs import CRED_FILE, WORKBOOK_NAME
    wb = Workbook(CRED_FILE, WORKBOOK_NAME)
    print(wb.all_sheets())
