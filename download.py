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

session = input("Insert your '_turner_session' key: ")
assert isinstance(session, str)
cache = "/tmp/"
header = {'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json, text/javascript, */*; q=0.01',
          'Cookie': '_turner_session=' + session}
books = {}
baseurl = "https://webapp.scuolabook.it/books"
data = requests.get(baseurl, headers=header).text

for i in range(len(re.findall('"id":(.*?),', data))):
    books[re.findall('"id":(.*?),', data)[i]] = re.findall(
        '"ws_title":"(.*?)"', data)[i].replace("\u0026", "&")

print("\n[Your library]\n")

for bookid in books:
    print("{}){}{}").format(bookid, " " * (7 - len(bookid)), books[bookid])

try:
    input = raw_input
except NameError:
    pass

bookid = input("\nInsert book ID to download: ")
assert isinstance(bookid, str)
bookid = int(bookid)
data = requests.get("{}/{}.json".format(
    baseurl, str(bookid)), headers=header).text
title = re.search('"ws_title":"(.*?)"', data).group(1)
author = re.search('"ws_author":"(.*?)"', data).group(1)
isbn = re.search('"ws_isbn":"(.*?)"', data).group(1)
npages = int(re.search('"ws_num_pages":"(.*?)"', data).group(1))
print("\n[Selected book]\n\nTitle: '{}'\nAuthor: {} "
      "\nISBN: isbn \nPages: {} \n".format(title, author, isbn, str(npages)))
data = ""
payload = ""

for i in range(1, npages + 2):
    if i % 100 == 0 or i == npages + 1:
        data += requests.get("{}/{}/pages?{}".format(
            baseurl, str(bookid), payload[1:]), headers=header).text
        payload = ""
    payload += "&pages[]=" + str(i)

pages = []
matches = re.findall('":"(.*?)"', data)

for match in matches:
    cpage = str(matches.index(match) + 1)
    print("\nDownloading page {}/{}...".format(cpage, str(npages)))
    sys.stdout.flush()
    link = match.replace("\\u0026", "&")
    filename = hashlib.md5(link).hexdigest()
    with open(cache + filename + ".jpg", "w") as f:
        f.write(requests.get(link).content)
    pages.append(filename)

print("\nConverting images to pdf format...")

for filename in pages:
    pdf_bytes = img2pdf.convert([cache + filename + ".jpg"])
    with open(cache + filename + ".pdf", "wb") as f:
        f.write(pdf_bytes)
    print("\n'{}.pdf' created!".format(filename))
    sys.stdout.flush()

merger = PyPDF2.PdfFileMerger()
print("\nMerging everything...")

for filename in pages:
    with open(cache + filename + ".pdf", "wb") as f:
        merger.append(PyPDF2.PdfFileReader(f))

merger.write(title + ".pdf")
print("Well done!")
