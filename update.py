from datetime import datetime
from traceback import format_exc

from bs4 import BeautifulSoup
from requests import get

from app import DB


def update():
    try:
        for key in ["films", "series", "cartoons", "animation"]:
            i = 1
            while True:
                try:
                    ua = {"User-Agent": "Mozilla/5.0 (Windows NT 6.2; Win64; x64) AppleWebKit/537.36 "
                                        "(KHTML, like Gecko) Chrome/32.0.1667.0 Safari/537.36"}
                    soup = BeautifulSoup(get(f"https://rezka.ag/{key}/page/{i}/", headers=ua).content,
                                         "html.parser")
                    search = soup.find_all(attrs={"class": "b-content__inline_item"})
                    if len(search) == 0:
                        break
                    for item in search:
                        try:
                            link = item.find(attrs={"class": "b-content__inline_item-link"})
                            split = str(link.div.string).split(", ")
                            find = item.find(attrs={"class": "b-content__inline_item-cover"})
                            info = find.find(attrs={"class": "info"})
                            title = {"_id": item["data-id"], "Ссылка": item["data-url"], "Название": link.a.string,
                                     "Год": split[0], "Страна": split[1], "Жанр": split[2]}
                            lists = {"films": [DB.db.films.insert_one(title), DB.db.serials.insert_one(title)],
                                     "series": [DB.db.films.insert_one(title), DB.db.serials.insert_one(title)],
                                     "cartoons": [DB.db.multfilms.insert_one(title),
                                                  DB.db.multserials.insert_one(title)],
                                     "animation": [DB.db.anime.insert_one(title), DB.db.animeserials.insert_one(title)]}
                            if info is None:
                                a = lists[key][0]
                            else:
                                b = lists[key][1]
                        except Exception:
                            print(format_exc())
                except Exception:
                    print(format_exc())
                i += 1
        DB.db.info.update_one({"_id": "Настройки"}, {"$set": {"Дата обновления": datetime.now()}})
    except Exception:
        print(format_exc())


if __name__ == "__main__":
    try:
        update()
    except Exception:
        print(format_exc())
