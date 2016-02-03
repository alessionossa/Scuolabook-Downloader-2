import requests,re,hashlib,sys,
import img2pdf #https://github.com/josch/img2pdf
import PyPDF2 #https://github.com/mstamy2/PyPDF2

session=raw_input("Your '_turner_session' key: ")
cache="/tmp/"

header={'X-Requested-With':'XMLHttpRequest','Accept':'application/json, text/javascript, */*; q=0.01','Cookie':'_turner_session='+session}
books={}
data=requests.get("https://webapp.scuolabook.it/books",headers=header).text
for i in range(len(re.findall('"id":(.*?),',data))):
	books[re.findall('"id":(.*?),',data)[i]]=re.findall('"ws_title":"(.*?)"',data)[i].replace("\u0026","&")

print "\n[Your library]\n"
for bookid in books:
	print bookid+")"+" "*(7-len(bookid))+books[bookid]

bookid=int(raw_input("\nInsert book ID to download: "))

data=requests.get("https://webapp.scuolabook.it/books/"+str(bookid)+".json",headers=header).text
title=re.search('"ws_title":"(.*?)"',data).group(1)
author=re.search('"ws_author":"(.*?)"',data).group(1)
isbn=re.search('"ws_isbn":"(.*?)"',data).group(1)
npages=int(re.search('"ws_num_pages":"(.*?)"',data).group(1))

print "\n[Selected book]\n\nTitle: '"+title+"'\nAuthor: "+author+"\nISBN: "+isbn+"\nPages: "+str(npages)+"\n"

data=""
payload=""
for i in range(1,npages+2):
	if i%100==0 or i==npages+1:
		data+=requests.get("https://webapp.scuolabook.it/books/"+str(bookid)+"/pages?"+payload[1:],headers=header).text
		payload=""
	payload+="&pages[]="+str(i)

pages=[]
matches=re.findall('":"(.*?)"',data)

for match in matches:
	sys.stdout.write("\rDownloading page "+str(matches.index(match)+1)+"/"+str(npages)+"...")
	sys.stdout.flush()
	link=match.replace("\\u0026","&")
	filename=hashlib.md5(link).hexdigest()
	f=open(cache+filename+".jpg","w")
	f.write(requests.get(link).content)
	f.close()
	pages.append(filename)

print "\nConverting images to pdf format..."
for filename in pages:
	pdf_bytes=img2pdf.convert([cache+filename+".jpg"])
	f=open(cache+filename+".pdf","wb")
	f.write(pdf_bytes)
	f.close()
	sys.stdout.write("\r'"+filename+".pdf' created!")
	sys.stdout.flush()

merger=PyPDF2.PdfFileMerger()
print "\nMerging everything..."
for filename in pages:
	merger.append(PyPDF2.PdfFileReader(open(cache+filename+'.pdf','rb')))
merger.write(title+".pdf")
print "Well done!"
