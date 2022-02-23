from models.printer import Printer


jobs = [
    {
    "printer_id": "820426c2955942ceb21d7e5628d5e5d0",
    "file": "PRODUTOS_OFICIAIS/TC/TC_2m.gcode",
    },
    {
    "printer_id": "1c30d3ab91544feba10beafae3edd7db",
    "file": "PRODUTOS_OFICIAIS/TC/TC_2g.gcode",
    },
    {
    "printer_id": "713e8c8e541049bc866a4af7e16c6b64",
    "file": "PRODUTOS_OFICIAIS/TC/TC_2v.gcode",
    }
]

print(Printer.set_all(jobs))
