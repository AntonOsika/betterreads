from collections import Counter
import pandas as pd
from tqdm import tqdm
import joblib

from requests import get
from bs4 import BeautifulSoup

base = 'https://goodreads.com'
user_url_template = 'https://www.goodreads.com/review/list/{}?sort=rating&view=reviews'
user = '25875977-anton-osika'

memory = joblib.Memory('/tmp/joblib')
get = memory.cache(get)


def get_reviewers(book_soup, n_users=50, min_n_stars=5):
    users = []
    reviews = book_soup.find_all('div', attrs={'class': 'left bodycol'})
    for review in reviews:
        # Count number of stars that have class p10
        try:
            n_stars = len([
                1 for x in list(
                    list(list(review.children)[1].children)[5].children)
                if 'p10' in x.attrs['class']
            ])
            if n_stars >= min_n_stars:
                user = list(
                    list(list(review.children)[1].children)
                    [3].children)[1].attrs['href']
                users.append(user.split('/')[-1])

                if len(users) >= n_users:
                    return users
        except (AttributeError, IndexError):
            pass

    return users


def get_books(user_id, n_books=20):
    response = get(user_url_template.format(user_id))

    user_soup = BeautifulSoup(response.text, 'html.parser')

    books = user_soup.find_all(
        name='a',
        attrs={
            'href': lambda x: x is not None and x.startswith('/book/show'),
            'title': lambda x: x is not None
        })

    return list(books)[:n_books]


user_books = get_books(user)

users = []
for book in (user_books):
    response = get(base + book.attrs['href'])
    book_soup = BeautifulSoup(response.text, 'html.parser')
    users += get_reviewers(book_soup)

print('users')
print(users)

liked_books = []
for user in (users):
    liked_books += get_books(user)

min_n_likes = 0
sorted_books = pd.Series(liked_books).value_counts().sort_values(
    ascending=False)
recommended = sorted_books[sorted_books >= min_n_likes]

# df = pd.DataFrame([{b.attrs['title']: {'likes': c, 'url': base + b.attrs['href']}} for b, c in zip(recommended.index, recommended)])

print('recommended')
titles = [b.attrs['title'] for b in recommended.index]
title_chars = max(map(len, titles)) + 5
for i in range(len(titles)):
    print(titles[i] + ' ' * (title_chars - len(titles[i])), recommended.iloc[i],
          '    ', base + recommended.index[i].attrs['href'])

# print(df)
