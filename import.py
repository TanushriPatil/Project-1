import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://qnalitaorxyhsv:468a321ec017bf050aba55b2453e65a882f782289c025d23223829e3268b22ba@ec2-18-233-32-61.compute-1.amazonaws.com:5432/d1e71pusba5ano")
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open("books.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
		{"isbn": isbn, "title": title, "author": author, "year": year})
        print(f"Added the book: ISBN: {isbn}, TITLE: {title}, AUTHOR: {author}, YEAR: {year}")
    db.commit()


if __name__ == "__main__":
    main()



