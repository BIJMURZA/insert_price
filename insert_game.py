import psycopg2
import requests
import pandas as pd
from bs4 import BeautifulSoup


def reformat_date(date):
    months = {'янв.': '1', 'фев.': '2', 'мар.': '3',
              'апр.': '4', 'мая.': '5', 'июн.': '6', 'июл.': '7',
              'авг.': '8', 'сен.': '9', 'окт.': '10',
              'ноя.': '11', 'дек.': '12'}
    month_number = months.get(date[1]).replace('.', '')
    return f"{date[0].zfill(2)}/{month_number.zfill(2)}/{date[2]}"


def insert_game(app, cursor):
    url = f"https://store.steampowered.com/app/{app}"
    response = requests.get(url, headers={'Accept-Language': 'ru-Ru'})
    soup = BeautifulSoup(response.content, "lxml")
    data_min = []
    data_rec = []
    title = soup.find("div", class_="apphub_AppName").text
    description = soup.find("div", class_="game_description_snippet").text.strip()
    developer = soup.find("div", id="developers_list").text.strip()
    publisher = soup.find_all("div", class_="dev_row")[1].find("div", class_="summary").text.strip()
    release = soup.find("div", class_="date").text.split()
    review = soup.find('span', class_="game_review_summary").text.strip()
    min_div = soup.find("div", class_="game_area_sys_req_leftCol")
    min_ul = min_div.find_all("ul", class_="bb_ul")
    for min_li in min_ul:
        min_req = min_li.find_all("li")
        for minimum_req in min_req:
            data_min.append(minimum_req.text.strip())
    rec_div = soup.find("div", class_="game_area_sys_req_rightCol")
    rec_ul = rec_div.find_all("ul", class_="bb_ul")
    for rec_li in rec_ul:
        rec_req = rec_li.find_all("li")
        for recommended_req in rec_req:
            data_rec.append(recommended_req.text.strip())
    update = """
            UPDATE games SET game_name = %s, description = %s, developer = %s,
            publisher = %s, release = TO_DATE(%s, 'DD/MM/YYYY'), review = %s, min_req = %s, rec_req = %s
            WHERE aid = %s;
            """
    cursor.execute(update, (title, description, developer, publisher, reformat_date(release), review,
                            '\n'.join(data_min), '\n'.join(data_rec), app, ))



if __name__ == "__main__":
    con = psycopg2.connect(dbname='rusync', user='admin',
                           password='1945', host='localhost')
    cursor = con.cursor()
    cursor.execute('SELECT aid FROM games')



    aid = []
    for row in cursor.fetchall():
        aid.append(row[0])


    for game_id in aid:
        insert_game(str(game_id), cursor)
        con.commit()


    cursor.close()
    con.close()
