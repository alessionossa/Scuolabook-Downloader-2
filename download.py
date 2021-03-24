import requests
import re
import hashlib
import sys
import img2pdf  # https://github.com/josch/img2pdf
import PyPDF2  # https://github.com/mstamy2/PyPDF2

try:
    input = raw_input
except NameError:
    pass
session = input("Your '_reader_session' key: ")
cache = "/tmp/"

header = {'X-Requested-With': 'XMLHttpRequest','Accept': 'application/json, text/javascript, */*; q=0.01','Cookie': '_reader_session=' + session}
books = {}
data = requests.get("https://webapp.scuolabook.it/books", headers=header).text
for i in range(len(re.findall('"id":(.*?),', data))):
    books[re.findall('"id":(.*?),', data)[i]] = re.findall('"ws_title":"(.*?)"', data)[i].replace("\u0026", "&")

print("\n[Your library]\n")
for bookid in books:
    print(bookid + ")" + " " * (7 - len(bookid)) + books[bookid])

try:
    input = raw_input
except NameError:
    pass
bookid = int(input("\nInsert book ID to download: "))

data = requests.get("https://webapp.scuolabook.it/books/" + str(bookid), headers=header).text
title = re.search('"ws_title":"(.*?)"', data).group(1).encode('utf-8')
author = re.search('"ws_author":"(.*?)"', data).group(1).encode('utf-8')
publisher = re.search('"ws_publisher":"(.*?)"', data).group(1).encode('utf-8')
isbn = re.search('"ws_isbn":"(.*?)"', data)
if isbn:
    isbn = isbn.group(1).encode('utf-8')
npages = int(re.search('"ws_num_pages":"(.*?)"', data).group(1).encode('utf-8'))

print("\n[Selected book]\n\nTitle: '{}'\nAuthor: {} \nPublisher: {} \nISBN: {} \nPages: {} \n".format(title, author, publisher, isbn, str(npages)))

data = ""
payload = ""
for i in range(1, npages + 2):
    if i % 100 == 0 or i == npages + 1:
         data += requests.get("https://webapp.scuolabook.it/books/" + str(bookid) + "/pages?" + payload[1:], headers=header).text
         payload = ""
    payload += "&pages[]=" + str(i)

pages = []
matches = re.findall('":"(.*?)"', data)

for match in matches:
    sys.stdout.write("\rDownloading page " + str(matches.index(match) + 1) + "/" + str(npages) + "...")
    sys.stdout.flush()
    link = match.replace("\\u0026", "&").encode('utf-8')
    filename = hashlib.md5(link).hexdigest()
    f = open(cache + filename + ".jpg", "wb")
    f.write(requests.get(link).content)
    f.close()
    pages.append(filename)

print("\nConverting images to pdf format...")
for filename in pages:
    try: #python 2.x
        pdf_bytes = img2pdf.convert([cache + filename + ".jpg"])
    except: #python 3.x
        pdf_bytes = img2pdf.convert(open(cache + filename + ".jpg","rb").read())
    f = open(cache + filename + ".pdf", "wb")
    f.write(pdf_bytes)
    f.close()
    sys.stdout.write("\r'" + filename + ".pdf' created!")
    sys.stdout.flush()

merger = PyPDF2.PdfFileMerger()
print("\nMerging everything...")
for filename in pages:
    merger.append(PyPDF2.PdfFileReader(open(cache + filename + '.pdf', 'rb')))
merger.write(title.decode() + ".pdf")
print("Well done!")
