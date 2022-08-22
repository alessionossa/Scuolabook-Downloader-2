from io import BytesIO
import re
import sys
import requests
import img2pdf
import PyPDF4
from rich.console import Console
from rich.progress import track

console = Console()

INPUT_SESSION = console.input("🍪  Your '_reader_session' key: ")
ENDPOINT_SCUOLABOOK = "https://webapp.scuolabook.it/books"
HEADER = {'X-Requested-With': 'XMLHttpRequest',
          'Accept': 'application/json, text/javascript, */*; q=0.01',
          'Cookie': f'_reader_session={INPUT_SESSION}'}


class Book:
    """
    A Book interface
    """

    def __init__(self):
        self.book_id: int = 0
        self.title: bytes = ''
        self.author: bytes = ''
        self.publisher: bytes = ''
        self.isbn: bytes = ''
        self.npages: int = 0


def get_books_list_data():
    """
    This function return a dictionary that contains all books present in your library
    """
    data = requests.get(ENDPOINT_SCUOLABOOK,
                        headers=HEADER).text
    books = {}
    for i in range(len(re.findall('"id":(.*?),', data))):
        books[re.findall('"id":(.*?),', data)[i]] = re.findall(
            '"ws_title":"(.*?)"', data)[i].replace("\u0026", "&")
    return books

def get_books_list(books_list_data: dict):
    """
    This function takes in input the `books_list_data` dictionary data that contains all books
    check if the `_reader_session` is valid and if don't exit the program.
    Format them in a readable user manner and output them
    so the user can choose what book wanna download
    """
    if books_list_data == {}:
        console.print(
            "❌  Your library is empty or your '_reader_session' key is expired")
        exit(255)
    console.print("\n📚  [b][Your library][/b]\n")
    for bookid in books_list_data:
        console.print(f"📗  ID:({bookid})  [b]{books_list_data[bookid]}[/b]")


def get_selected_book(books_list_data: dict):
    """
    This function takes in input the `books_list_data` dictionary data that contains all books
    check if the `input_book_id` is valid and  present in the library if don't exit the program.
    Output to the user all the information about the book selected and return a book object
    """
    try:
        input_book_id = int(console.input(
            "\n🔢  Insert ID of the book to download them: "))
        for bookid in books_list_data:
            if not input_book_id != bookid:
                raise ValueError
    except ValueError:
        console.print("❌  Invalid Book ID")
        exit(255)
    book = Book()
    data = requests.get(
        f"{ENDPOINT_SCUOLABOOK}/{input_book_id}", headers=HEADER).text
    book.book_id = input_book_id
    book.title = re.search('"ws_title":"(.*?)"', data).group(1).encode('utf-8')
    book.author = re.search('"ws_author":"(.*?)"',
                            data).group(1).encode('utf-8')
    book.publisher = re.search(
        '"ws_publisher":"(.*?)"', data).group(1).encode('utf-8')
    book.isbn = re.search('"ws_isbn":"(.*?)"', data)
    if book.isbn:
        book.isbn = book.isbn.group(1).encode('utf-8')
    book.npages = int(re.search('"ws_num_pages":"(.*?)"',
                      data).group(1).encode('utf-8'))
    console.print("\n[Selected book]\n")
    console.print(f"📖  Title: {book.title.decode()}")
    console.print(f"👤  Author: {book.author.decode()}")
    console.print(f"🏛️  Publisher: {book.publisher.decode()}")
    console.print(f"📜  ISBN: {book.isbn.decode()}")
    console.print(f"📄  Pages: {book.npages}")
    return book

def get_all_pages(book: Book):
    """
    This function take in input a `Book` object  and return a list of page link to download
    """
    data  = ""
    payload = ""
    for i in track(range(1, book.npages + 2)):
        if i % 100 == 0 or i == book.npages + 1:
            data += requests.get(
                f"{ENDPOINT_SCUOLABOOK}/{book.book_id}/pages?{payload[1:]}", headers=HEADER).text
            payload = ""
        payload += f"&pages[]={i}"
    matches = re.findall('":"(.*?)"', data)
    return matches


def dowload_convert_all_pages(book: Book, matches: list):
    """
    This function takes as input a `Book` object and a list of links of pages
    and return a `list` that contains each PDF page in bytes format
    """
    pdfs_bytes = []
    for match in matches:
        console.print(
            f"\r📥  Downloading & Converting page {matches.index(match) + 1}/{book.npages}...")
        sys.stdout.flush()
        link = match.replace("\\u0026", "&").encode('utf-8')
        pdf_bytes = img2pdf.convert(requests.get(link).content)
        pdfs_bytes.append(pdf_bytes)
    return pdfs_bytes


def merging_pdf(pdfs_bytes: list, book: Book):
    """
    This function takes as input a `list` of PDF page of book in bytes format and `Book` object
    each element of the `list` is read and merged with the previous one and at the end of the `list`
    the final merged Book (PDF) is created
    """
    merger = PyPDF4.PdfFileMerger(strict=False)
    output_file = book.title.decode().replace('\u007C', '') + ".pdf"
    console.print("\n☯️  Merging everything...")
    for pdf_bytes in pdfs_bytes:
        with BytesIO(pdf_bytes) as pdf_file:
            pdf_file_stream = PyPDF4.PdfFileReader(
                stream=pdf_file, strict=False)
            merger.append(pdf_file_stream)
    console.print(f"⌛  Creating merged book ''{output_file}''...")
    merger.write(output_file)
    console.print(
        f":thumbs_up:  The book: ''{output_file}'' was created succesfully!")


def main():
    """
    This function execute all program
    """
    books_list_data = get_books_list_data()
    get_books_list(books_list_data=books_list_data)
    book = get_selected_book(books_list_data=books_list_data)
    matches = get_all_pages(book=book)
    pdfs_bytes = dowload_convert_all_pages(book=book, matches=matches)
    merging_pdf(pdfs_bytes=pdfs_bytes, book=book)

if __name__ == '__main__':
    main()
