import win32print

def tampilkan_semua_printer():
    print("=== DAFTAR PRINTER YANG TERHUBUNG DI WINDOWS ===\n")
    
    printers = win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)
    
    printer_default = win32print.GetDefaultPrinter()
    
    for printer in printers:
        nama_printer = printer[2]
        
        if nama_printer == printer_default:
            print(f" -> [DEFAULT] {nama_printer}")
        else:
            print(f" -> {nama_printer}")

if __name__ == "__main__":
    tampilkan_semua_printer()