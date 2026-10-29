"""Microsoft Word COM adapter that converts DOCX to PDF without showing UI."""

from pathlib import Path


class WordComConverter:
    def convert_to_pdf(self, source: Path, destination: Path):
        import pythoncom
        import win32com.client

        word = None
        document = None
        pythoncom.CoInitialize()
        try:
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            document = word.Documents.Open(
                str(source), ReadOnly=True, AddToRecentFiles=False, Visible=False
            )
            document.ExportAsFixedFormat(str(destination), 17)
        finally:
            if document is not None:
                try:
                    document.Close(False)
                except Exception:
                    pass
            if word is not None:
                try:
                    word.Quit()
                except Exception:
                    pass
            pythoncom.CoUninitialize()
