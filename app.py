import sys
from argparse import ArgumentParser
from datetime import datetime
from functools import partial
from hashlib import sha256
from os import execl
from re import findall, sub
from time import sleep
from traceback import format_exc

from pymongo import MongoClient, ASCENDING
from pywebio import config, start_server
from pywebio.input import NUMBER, TEXT, PASSWORD
from pywebio.output import put_tabs
from pywebio.output import put_text, put_processbar, set_processbar, put_scrollable, put_table, use_scope, put_link
from pywebio.output import toast, close_popup, clear, put_collapse, put_scope, popup, put_row, put_button, PopupSize
from pywebio.pin import put_input, put_checkbox, pin_on_change, pin_update, pin
from pywebio.session import run_js, local
from pywebio_battery import set_cookie, get_cookie

import update

DB = MongoClient("")


def delete(self=None, tab=None, tid=None, name=None):
    try:
        if tab == "Фильмы":
            DB.myanime.films.delete_one({"_id": tid})
        if tab == "Мультфильмы":
            DB.myanime.multfilms.delete_one({"_id": tid})
        if tab == "Сериалы":
            DB.myanime.serials.delete_one({"_id": tid})
        if tab == "Мультсериалы":
            DB.myanime.multserials.delete_one({"_id": tid})
        if tab == "Аниме":
            DB.myanime.anime.delete_one({"_id": tid})
        if tab == "Анимесериалы":
            DB.myanime.animeserials.delete_one({"_id": tid})
        toast(f"{name} успешно удален из раздела {tab}!", color="success")
        close_popup()
        table()
    except Exception:
        toast(f"{name} не получилось удалить из раздела {tab}!", color="warn")
        print(format_exc())


def save(name=None, tab=None, title=None):
    try:
        if name == "Сохранить":
            for key in local["list"].keys():
                title = None
                if tab == "Фильмы":
                    title = DB.db.films.find_one({"_id": key})
                    DB.myanime.films.insert_one(title)
                if tab == "Мультфильмы":
                    title = DB.db.multfilms.find_one({"_id": key})
                    DB.myanime.multfilms.insert_one(title)
                if tab == "Сериалы":
                    title = DB.db.serials.find_one({"_id": key})
                    title.update({"Сезоны": local["list"][key]})
                    DB.myanime.serials.insert_one(title)
                if tab == "Мультсериалы":
                    title = DB.db.multserials.find_one({"_id": key})
                    title.update({"Сезоны": local["list"][key]})
                    DB.myanime.multserials.insert_one(title)
                if tab == "Аниме":
                    title = DB.db.anime.find_one({"_id": key})
                    DB.myanime.anime.insert_one(title)
                if tab == "Анимесериалы":
                    title = DB.db.animeserials.find_one({"_id": key})
                    title.update({"Сезоны": local["list"][key]})
                    DB.myanime.animeserials.insert_one(title)
                toast(f"{title['Название']} успешно сохранен в раздел {tab}!", color="success")
        if name == "Обновить":
            if tab == "Фильмы":
                DB.myanime.films.replace_one({"_id": local["list"]["_id"]}, local["list"])
            if tab == "Мультфильмы":
                DB.myanime.multfilms.replace_one({"_id": local["list"]["_id"]}, local["list"])
            if tab == "Сериалы":
                DB.myanime.serials.replace_one({"_id": local["list"]["_id"]}, local["list"])
            if tab == "Мультсериалы":
                DB.myanime.multserials.replace_one({"_id": local["list"]["_id"]}, local["list"])
            if tab == "Аниме":
                DB.myanime.anime.replace_one({"_id": local["list"]["_id"]}, local["list"])
            if tab == "Анимесериалы":
                DB.myanime.animeserials.replace_one({"_id": local["list"]["_id"]}, local["list"])
            toast(f"{title['Название']} успешно обновлен в разделе {tab}!", color="success")
        local["list"].clear()
        close_popup()
        table()
    except Exception:
        toast(f"{title['Название']} не получилось обновить в разделе {tab}!", color="warn")
        print(format_exc())


def seasonsedit(count=None, typ=None, item=None, scope=None, season=None):
    try:
        if typ == "seasons":
            clear(scope=scope)
            i = 1
            for x in range(count):
                if f"Сезон {x + 1}" in item["Сезоны"]:
                    ss = ["Все"]
                    for xx in range(item["Сезоны"][f"Сезон {x + 1}"]["Серий"]):
                        ss.append(f"Серия {xx + 1}")
                    put_collapse(title=f"Сезон {x + 1}:", scope=scope, content=[
                        put_input(name=f"series{i}", label="Количество серий в сезоне:",
                                  value=item["Сезоны"][f"Сезон {x + 1}"]["Серий"], type=NUMBER),
                        put_scope(name=f"scope{i}", content=[
                            put_checkbox(name=f"watch{i}", options=ss, label="Просмотрено серий в сезоне:",
                                         value=[x for x in item["Сезоны"][f"Сезон {x + 1}"]["Просмотрено"]])])])
                    pin_on_change(name=f"watch{i}", clear=True,
                                  onchange=partial(seasonsedit, typ="check", item=item, season=i))
                else:
                    put_collapse(title=f"Сезон {x + 1}:", scope=scope, content=[
                        put_input(name=f"series{i}", label="Количество серий в сезоне:", type=NUMBER),
                        put_scope(name=f"scope{i}", content=[])])
                    local["list"]["Сезоны"].update({f"Сезон {x + 1}": {"Серий": 0, "Просмотрено": []}})
                pin_on_change(name=f"series{i}", clear=True,
                              onchange=partial(seasonsedit, typ="series", scope=f"scope{i}", item=item, season=i))
                i += 1
        if typ == "series":
            clear(scope=scope)
            ss = ["Все"]
            for x in range(count):
                ss.append(f"Серия {x + 1}")
            if f"Сезон {season}" in item["Сезоны"]:
                put_checkbox(name=f"watch{season}", scope=scope, options=ss, label="Просмотрено серий в сезоне:",
                             value=[x for x in item["Сезоны"][f"Сезон {season}"]["Просмотрено"]])
            else:
                put_checkbox(name=f"watch{season}", scope=scope, options=ss, label="Просмотрено серий в сезоне:")
            pin_on_change(name=f"watch{season}", clear=True,
                          onchange=partial(seasonsedit, typ="check", item=item, season=season))
            local["list"]["Сезоны"][f"Сезон {season}"].update({"Серий": count})
        if typ == "check":
            local["list"]["Сезоны"][f"Сезон {season}"].update({"Просмотрено": count})
    except Exception:
        print(format_exc())


def edit(self=None, tab=None, tid=None):
    try:
        db, local["list"] = {"Фильмы": DB.myanime.films.find_one({"_id": tid}),
                             "Мультфильмы": DB.myanime.multfilms.find_one({"_id": tid}),
                             "Сериалы": DB.myanime.serials.find_one({"_id": tid}),
                             "Мультсериалы": DB.myanime.multserials.find_one({"_id": tid}),
                             "Аниме": DB.myanime.anime.find_one({"_id": tid}),
                             "Анимесериалы": DB.myanime.animeserials.find_one({"_id": tid})}, {}
        local["list"].clear()
        button1 = put_button(label="Сохранить", onclick=partial(save, name="Обновить", tab=tab), color="success")
        button2 = put_button(label="Удалить", color="danger",
                             onclick=partial(delete, tab=tab, tid=db[tab]["_id"], name=db[tab]["Название"]))
        if tab in ["Фильмы", "Мультфильмы", "Аниме"]:
            popup(title=f"Изменить {db[tab]['Название']}:",
                  content=[put_input(name="name", label="Название:", type=TEXT, value=db[tab]["Название"],
                                     readonly=True),
                           put_input(name="url", label="Ссылка:", type=TEXT, value=db[tab]["Ссылка"], readonly=True),
                           put_input(name="year", label="Год:", type=TEXT, value=db[tab]["Год"], readonly=True),
                           put_input(name="country", label="Страна:", type=TEXT, value=db[tab]["Страна"],
                                     readonly=True),
                           put_input(name="genre", label="Жанр:", type=TEXT, value=db[tab]["Жанр"], readonly=True),
                           put_row(size="99px 10fr 81px", content=[button1, None, button2])], size=PopupSize.NORMAL)
        if tab in ["Сериалы", "Мультсериалы", "Анимесериалы"]:
            s, i = [], 1
            for key in db[tab]["Сезоны"].keys():
                ss = ["Все"]
                for x in range(db[tab]["Сезоны"][key]["Серий"]):
                    ss.append(f"Серия {x + 1}")
                s.append(put_collapse(title=f"{key}:", content=[
                    put_input(name=f"series{i}", label="Количество серий в сезоне:",
                              value=db[tab]["Сезоны"][key]["Серий"], type=NUMBER),
                    put_scope(name=f"scope{i}", content=[
                        put_checkbox(name=f"watch{i}", options=ss, label="Просмотрено серий в сезоне:",
                                     value=[x for x in db[tab]["Сезоны"][key]["Просмотрено"]])])]))
                pin_on_change(name=f"series{i}", clear=True,
                              onchange=partial(seasonsedit, typ="series", scope=f"scope{i}", item=db[tab], season=i))
                pin_on_change(name=f"watch{i}", clear=True,
                              onchange=partial(seasonsedit, typ="check", item=db[tab], season=i))
                i += 1
            local["list"].update(db[tab])
            popup(title=f"Изменить {db[tab]['Название']}:",
                  content=[put_input(name="name", label="Название:", type=TEXT, value=db[tab]["Название"],
                                     readonly=True),
                           put_input(name="url", label="Ссылка:", type=TEXT, value=db[tab]["Ссылка"], readonly=True),
                           put_input(name="year", label="Год:", type=TEXT, value=db[tab]["Год"], readonly=True),
                           put_input(name="country", label="Страна:", type=TEXT, value=db[tab]["Страна"],
                                     readonly=True),
                           put_input(name="genre", label="Жанр:", type=TEXT, value=db[tab]["Жанр"], readonly=True),
                           put_input(name="seasons", label="Количество сезонов:", type=NUMBER,
                                     value=len(db[tab]["Сезоны"])), put_scope(name="season", content=s),
                           put_row(size="99px 10fr 81px", content=[button1, None, button2])], size=PopupSize.NORMAL)
            pin_on_change(name="seasons", clear=True,
                          onchange=partial(seasonsedit, typ="seasons", scope="season", item=db[tab]))
    except Exception:
        print(format_exc())


def seriesupdate(count=None, tid=None, season=None):
    try:
        local["list"][tid][f"Сезон {season}"].update({"Просмотрено": count})
    except Exception:
        print(format_exc())


def selector(count=None, tid=None, season=None):
    try:
        local["list"][tid].update({f"Сезон {season}": {"Серий": count, "Просмотрено": []}})
        clear(scope=f"series{tid}s{season}")
        serieslist = ["Все"]
        for x in range(count):
            serieslist.append(f"Серия {x + 1}")
        put_checkbox(name=f"select{tid}s{season}", options=serieslist, label="Просмотрено серий в сезоне:",
                     scope=f"series{tid}s{season}")
        pin_on_change(name=f"select{tid}s{season}", clear=True, onchange=partial(seriesupdate, tid=tid, season=season))
    except Exception:
        print(format_exc())


def seasons(count=None, tid=None):
    try:
        clear(scope=f"season{tid}")
        for x in range(count):
            put_collapse(title=f"Сезон {x + 1}:", scope=f"season{tid}", content=[
                put_input(name=f"series{tid}s{x + 1}", label="Количество серий в сезоне:", type=NUMBER),
                put_scope(name=f"series{tid}s{x + 1}", content=[])])
            pin_on_change(name=f"series{tid}s{x + 1}", clear=True, onchange=partial(selector, tid=tid, season=x + 1))
    except Exception:
        print(format_exc())


def collapse(name=None, datalist=None, tab=None):
    try:
        if name in datalist:
            alldb = {"Фильмы": DB.db.films.find_one(
                {"Название": sub(r" \([\w\- ,.]+, \w+, \w+\)", "", name)}),
                "Мультфильмы": DB.db.multfilms.find_one(
                    {"Название": sub(r" \([\w\- ,.]+, \w+, \w+\)", "", name)}),
                "Сериалы": DB.db.serials.find_one(
                    {"Название": sub(r" \([\w\- ,.]+, \w+, \w+\)", "", name)}),
                "Мультсериалы": DB.db.multserials.find_one(
                    {"Название": sub(r" \([\w\- ,.]+, \w+, \w+\)", "", name)}),
                "Аниме": DB.db.anime.find_one(
                    {"Название": sub(r" \([\w\- ,.]+, \w+, \w+\)", "", name)}),
                "Анимесериалы": DB.db.animeserials.find_one(
                    {"Название": sub(r" \([\w\- ,.]+, \w+, \w+\)", "", name)})}
            if tab in ["Фильмы", "Мультфильмы", "Аниме"]:
                if alldb[tab]["_id"] not in local["list"]:
                    put_collapse(title=name, scope="items", content=[
                        put_input(name=f"name{alldb[tab]['_id']}", label="Название:", type=TEXT,
                                  value=alldb[tab]["Название"], readonly=True),
                        put_input(name=f"url{alldb[tab]['_id']}", label="Ссылка:", type=TEXT,
                                  value=alldb[tab]["Ссылка"], readonly=True),
                        put_input(name=f"year{alldb[tab]['_id']}", label="Год:", type=TEXT,
                                  value=alldb[tab]["Год"], readonly=True),
                        put_input(name=f"country{alldb[tab]['_id']}", label="Страна:", type=TEXT,
                                  value=alldb[tab]["Страна"], readonly=True),
                        put_input(name=f"genre{alldb[tab]['_id']}", label="Жанр:", type=TEXT,
                                  value=alldb[tab]["Жанр"], readonly=True)])
                    pin_update(name="list", value="")
                    local["list"].update({alldb[tab]["_id"]: {}})
                else:
                    pin_update(name="list", value="")
            if tab in ["Сериалы", "Мультсериалы", "Анимесериалы"]:
                if alldb[tab]["_id"] not in local["list"]:
                    put_collapse(title=name, scope="items", content=[
                        put_scope(name=f"serial{alldb[tab]['_id']}", content=[
                            put_input(name=f"name{alldb[tab]['_id']}", label="Название:", type=TEXT,
                                      value=alldb[tab]["Название"], readonly=True),
                            put_input(name=f"url{alldb[tab]['_id']}", label="Ссылка:", type=TEXT,
                                      value=alldb[tab]["Ссылка"], readonly=True),
                            put_input(name=f"year{alldb[tab]['_id']}", label="Год:", type=TEXT,
                                      value=alldb[tab]["Год"], readonly=True),
                            put_input(name=f"country{alldb[tab]['_id']}", label="Страна:", type=TEXT,
                                      value=alldb[tab]["Страна"], readonly=True),
                            put_input(name=f"genre{alldb[tab]['_id']}", label="Жанр:", type=TEXT,
                                      value=alldb[tab]["Жанр"], readonly=True),
                            put_input(name=f"seasons{alldb[tab]['_id']}", label="Количество сезонов:", type=NUMBER),
                            put_scope(name=f"season{alldb[tab]['_id']}", content=[])])])
                    pin_on_change(name=f"seasons{alldb[tab]['_id']}", clear=True,
                                  onchange=partial(seasons, tid=alldb[tab]["_id"]))
                    pin_update(name="list", value="")
                    local["list"].update({alldb[tab]["_id"]: {}})
                else:
                    pin_update(name="list", value="")
    except Exception:
        print(format_exc())


def add(self=None, tab=None):
    try:
        alldb = {"Фильмы": [DB.db.films.find().sort("Название", ASCENDING), DB.db.films.count_documents({})],
                 "Мультфильмы": [DB.db.multfilms.find().sort("Название", ASCENDING),
                                 DB.db.multfilms.count_documents({})],
                 "Сериалы": [DB.db.serials.find().sort("Название", ASCENDING), DB.db.serials.count_documents({})],
                 "Мультсериалы": [DB.db.multserials.find().sort("Название", ASCENDING),
                                  DB.db.multserials.count_documents({})],
                 "Аниме": [DB.db.anime.find().sort("Название", ASCENDING), DB.db.anime.count_documents({})],
                 "Анимесериалы": [DB.db.animeserials.find().sort("Название", ASCENDING),
                                  DB.db.animeserials.count_documents({})]}
        mydb, local["list"] = {"Фильмы": DB.myanime.films.find().sort("Название", ASCENDING),
                               "Мультфильмы": DB.myanime.multfilms.find().sort("Название", ASCENDING),
                               "Сериалы": DB.myanime.serials.find().sort("Название", ASCENDING),
                               "Мультсериалы": DB.myanime.multserials.find().sort("Название", ASCENDING),
                               "Аниме": DB.myanime.anime.find().sort("Название", ASCENDING),
                               "Анимесериалы": DB.myanime.animeserials.find().sort("Название", ASCENDING)}, {}
        local["list"].clear()
        popup(title=f"Добавить {tab}:", content=[put_text("Подождите, идет загрузка..."),
                                                 put_processbar(name="bar", init=0)], size=PopupSize.NORMAL)
        datalist, i, tables = [], 1, [x["Название"] for x in mydb[tab]]
        for item in alldb[tab][0]:
            set_processbar(name="bar", value=((i * 100) / alldb[tab][1]) / 100)
            if item['Название'] not in tables:
                datalist.append(f"{item['Название']} ({item['Год']}, {item['Страна']}, {item['Жанр']})")
            i += 1
        popup(title=f"Добавить {tab}:",
              content=[put_input(name="list", label="Название:", type=TEXT, datalist=datalist),
                       put_scope(name="scope", content=[put_scrollable(content=[
                           put_scope(name="items", content=[])], keep_bottom=True, border=False)]),
                       put_button(label="Сохранить", onclick=partial(save, name="Сохранить", tab=tab),
                                  color="success")], size=PopupSize.NORMAL)
        pin_on_change(name="list", clear=True, onchange=partial(collapse, datalist=datalist, tab=tab))
    except Exception:
        print(format_exc())


def series(item=None):
    try:
        tab, count = [], 0
        for key in item["Сезоны"].keys():
            lens = None
            if "Все" in item["Сезоны"][key]["Просмотрено"]:
                lens = "Все"
            else:
                lens = len(item["Сезоны"][key]["Просмотрено"])
            tab.append([f"{key} ({lens} из {item['Сезоны'][key]['Серий']}):"])
            if "Все" in item["Сезоны"][key]["Просмотрено"]:
                for i in range(item["Сезоны"][key]["Серий"]):
                    tab.append(["", f"Серия {i + 1}"])
                    count += 1
            else:
                for part in item["Сезоны"][key]["Просмотрено"]:
                    tab.append(["", part])
                    count += 1
        return put_collapse(title=f"{count}", content=[put_table(tab)])
    except Exception:
        print(format_exc())


@use_scope("table", clear=True)
def table(query=None):
    try:
        db, tabs = {"Фильмы": [DB.myanime.films.find().sort("Название", ASCENDING), []],
                    "Мультфильмы": [DB.myanime.multfilms.find().sort("Название", ASCENDING), []],
                    "Сериалы": [DB.myanime.serials.find().sort("Название", ASCENDING), []],
                    "Мультсериалы": [DB.myanime.multserials.find().sort("Название", ASCENDING), []],
                    "Аниме": [DB.myanime.anime.find().sort("Название", ASCENDING), []],
                    "Анимесериалы": [DB.myanime.animeserials.find().sort("Название", ASCENDING), []]}, []
        for key in db.keys():
            if key in ["Фильмы", "Мультфильмы", "Аниме"]:
                db[key][1].append(["Название", "Год", "Страна", "Жанр"])
                for item in db[key][0]:
                    item = dict(item)
                    if query is not None:
                        if len(findall(query.lower(), item["Название"].lower())) != 0:
                            if local["admin"]:
                                db[key][1].append([
                                    put_link(name=item["Название"], url=item["Ссылка"], new_window=True), item["Год"],
                                    item["Страна"], item["Жанр"],
                                    put_button(label="Редактировать", color="warning",
                                               onclick=partial(edit, tab=key, tid=item["_id"]))])
                            else:
                                db[key][1].append([
                                    put_link(name=item["Название"], url=item["Ссылка"], new_window=True),
                                    item["Год"], item["Страна"], item["Жанр"]])
                    else:
                        if local["admin"]:
                            db[key][1].append([put_link(name=item["Название"], url=item["Ссылка"], new_window=True),
                                               item["Год"], item["Страна"], item["Жанр"],
                                               put_button(label="Редактировать", color="warning",
                                                          onclick=partial(edit, tab=key, tid=item["_id"]))])
                        else:
                            db[key][1].append([put_link(name=item["Название"], url=item["Ссылка"], new_window=True),
                                               item["Год"], item["Страна"], item["Жанр"]])
            if key in ["Сериалы", "Мультсериалы", "Анимесериалы"]:
                db[key][1].append(["Название", "Год", "Страна", "Жанр", "Сезоны", "Серии", "Просмотрено"])
                for item in db[key][0]:
                    item, serieses = dict(item), 0
                    for season in item["Сезоны"]:
                        serieses += item["Сезоны"][season]["Серий"]
                    if query is not None:
                        if len(findall(query.lower(), item["Название"].lower())) != 0:
                            if local["admin"]:
                                db[key][1].append([
                                    put_link(name=item["Название"], url=item["Ссылка"], new_window=True), item["Год"],
                                    item["Страна"], item["Жанр"], len(item["Сезоны"]), serieses, series(item),
                                    put_button(label="Редактировать", color="warning",
                                               onclick=partial(edit, tab=key, tid=item["_id"]))])
                            else:
                                db[key][1].append([
                                    put_link(name=item["Название"], url=item["Ссылка"], new_window=True), item["Год"],
                                    item["Страна"], item["Жанр"], len(item["Сезоны"]), serieses, series(item)])
                    else:
                        if local["admin"]:
                            db[key][1].append([put_link(name=item["Название"], url=item["Ссылка"], new_window=True),
                                               item["Год"], item["Страна"], item["Жанр"], len(item["Сезоны"]), serieses,
                                               series(item),
                                               put_button(label="Редактировать", color="warning",
                                                          onclick=partial(edit, tab=key, tid=item["_id"]))])
                        else:
                            db[key][1].append([put_link(name=item["Название"], url=item["Ссылка"], new_window=True),
                                               item["Год"], item["Страна"], item["Жанр"], len(item["Сезоны"]), serieses,
                                               series(item)])
            if local["admin"]:
                tabs.append({"title": key, "content": [put_table(db[key][1]),
                                                       put_button(label="Добавить", color="success",
                                                                  onclick=partial(add, tab=key))]})
            else:
                tabs.append({"title": key, "content": [put_table(db[key][1])]})
        clear(scope="table")
        put_tabs(tabs=tabs)
    except Exception:
        print(format_exc())


def auth(login=None, password=None, check=None):
    try:
        users = DB.db.info.find_one({"_id": "Пользователи"})
        if sha256(password.encode("utf-8")).hexdigest() == users[login]:
            toast(f"Добро пожаловать, {login}!", color="info")
            if len(check) != 0:
                set_cookie("User", login, days=30)
                set_cookie("Token", users[login], days=30)
                local["admin"] = True
                close_popup()
                search()
                table()
            else:
                set_cookie("User", login, days=30)
                clear(scope="search")
                local["admin"] = True
                close_popup()
                search()
                table()
        else:
            toast("Логин/Пароль неверные!", color="error")
    except Exception:
        toast("Логин/Пароль неверные!", color="error")
        print(format_exc())


@use_scope("search", clear=True)
def search():
    try:
        db, button = {"Фильмы": DB.db.films.count_documents({}),
                      "Мультфильмы": DB.db.multfilms.count_documents({}),
                      "Сериалы": DB.db.serials.count_documents({}),
                      "Мультсериалы": DB.db.multserials.count_documents({}),
                      "Аниме": DB.db.anime.count_documents({}),
                      "Анимесериалы": DB.db.animeserials.count_documents({})}, None
        if local["admin"]:
            button1 = put_button(label="Обновить БД", color="info",
                                 onclick=lambda: (toast("Вся база данных обновляется!", color="info"), update.update()))
            button2 = put_button(label="Перезагрузить программу", color="warning",
                                 onclick=lambda: (toast("Перезагрузка!", color="error"), sleep(1),
                                                  execl(sys.executable, "python", "app.py", *sys.argv[1:])))
            button3 = put_button(label="Выйти", color="danger",
                                 onclick=lambda: (set_cookie("User", None, days=30), set_cookie("Token", None, days=30),
                                                  close_popup(), main()))
            delta, status = datetime.now() - DB.db.info.find_one({"_id": "Настройки"})["Дата обновления"], None
            if delta.days <= 30:
                status = "Актуально"
            else:
                status = "Не актуально"
            time, stat = DB.db.info.find_one({"_id": "Настройки"})["Дата обновления"].strftime("%d.%m.%Y %H:%M:%S"), []
            for key in db.keys():
                stat.append(f"{key}: {db[key]}\n")
            button = put_button(label=get_cookie("User"), color="dark",
                                onclick=lambda: popup(title=f"Вы вошли как: {get_cookie('User')}", content=[
                                    put_text(f"Статистика БД:\n\n{''.join(stat)}\nПоследнее обновление: {time}\n"
                                             f"Статус: {status}"),
                                    put_row(content=[button1, None, button2, None, button3],
                                            size="117px 10fr 208px 10fr 69px")]))
        else:
            button4 = put_button(label="Войти", color="warning",
                                 onclick=lambda: auth(pin.login, pin.password, pin.save))
            button = put_button(label="Войти", color="dark",
                                onclick=lambda: popup(title="Вход:", content=[
                                    put_input(name="login", label="Логин:", type=TEXT),
                                    put_input(name="password", label="Пароль:", type=PASSWORD),
                                    put_checkbox(name="save", options=["Запомнить"]), button4]))
        put_row(content=[put_input(name="search", placeholder="Поиск", type=TEXT), None, button],
                size="10fr 0.25fr 102px")
        pin_on_change(name="search", clear=True, onchange=partial(table))
    except Exception:
        print(format_exc())


@config(theme="dark", title="My Anime List")
def main():
    try:
        users = DB.db.info.find_one({"_id": "Пользователи"})
        run_js("WebIO._state.CurrentSession.on_session_close(()=>{setTimeout(()=>location.reload(), 3000)})")
        if get_cookie("Token") == users[get_cookie("User")]:
            toast(f"Добро пожаловать, {get_cookie('User')}!", color="info")
            local["admin"] = True
            search()
            table()
        else:
            local["admin"] = False
            search()
            table()
    except Exception:
        local["admin"] = False
        search()
        table()
        print(format_exc())


if __name__ == "__main__":
    try:
        parser = ArgumentParser()
        parser.add_argument("-p", "--port", type=int, default=80)
        start_server(main, port=parser.parse_args().port, websocket_ping_interval=30)
    except Exception:
        print(format_exc())
