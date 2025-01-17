#!/usr/bin/env python3
import argparse
import glob
import json
import os
import re
from collections import defaultdict
from datetime import date, timedelta, datetime

OVERVIEW_COUNT = 10


# Common things ---------------------------------------------------------------
# See main at bottom
class ManualChange:
    """
    Apply a change to a range of menus in the v2 API. v1 is not supported.
    """

    def __init__(self, replacer, resto, start, end, all_days=False):
        """
        :param replacer: The function that will do the replacements. It will receive the path to the file and the
        original menu.
        :param start: The start date (inclusive).
        :param end: The end date (inclusive).
        :param resto: Which restaurant(s) to apply to.
        :param all_days: If the message should be added for all weekdays in the range. If false (the default), the
        changes will only be applied if there already is a menu for the day.
        """
        self.replacer = replacer
        self.start = start
        self.end = end
        self.resto = resto
        if isinstance(self.resto, str):
            self.resto = [self.resto]
        assert isinstance(self.resto, list)
        self.all_days = all_days

    def is_applicable(self, menu_date):
        """Check if this change is applicable to the given date"""
        return self.start <= menu_date <= self.end

    def date_range(self):
        """Return an iterator over the applicable range. Only weekdays are returned."""
        for n in range(int((self.end - self.start).days) + 1):
            result = self.start + timedelta(n)
            if result.weekday() < 5:
                yield result


# Restjesmaand Zomer 18
# Sint-Jansvest die geen menu meer serveert, alleen overschotten.
def restjesmaand18_replacer(_path, original):
    # original: {"date": "2018-06-14", "meals": [], "open": false, "vegetables": []}

    name = ("Om voedseloverschotten op het einde van het academiejaar te beperken, "
            "kunnen we geen dagmenu presenteren. "
            "Ga langs en laat je verrassen door ons keukenpersoneel.")

    return {
        "message": name,
        "date": original["date"],
        "meals": [],
        "open": True,
        "vegetables": [],
    }


# Paasvakantie 2019
def paasvakantie19_general(_path, original):
    original['message'] = ("Tijdens de paasvakantie zijn resto's Campus Sterre en Campus Merelbeke geopend als "
                           "cafetaria.")
    original['open'] = True
    return original


def paasvakantie19_en(_path, original):
    original['message'] = 'During the Easter Holiday restos Campus Sterre and Campus Merelbeke operate as cafetaria.'
    original['open'] = True
    return original


def paasvakantie19_brug(_path, original):
    original['message'] = "Tijdens de paasvakantie is De Brug enkel 's middags geopend."
    return original


# Werken in De Brug waardoor de resto gesloten is.
def werken_brug19_replacer(_path, original):
    message = ('De Brug sluit van 20 mei tot 30 september 2019 voor verbouwingswerken. Tijdens de sluiting neemt resto '
               'Kantienberg de functies en het aanbod van de Brug over, zoals de avondopening.')
    return {
        "message": message,
        "date": original["date"],
        "open": False
    }


def werken_brug19_replacer2(_path, original):
    message = ("Resto De Brug en Cafetaria De Brug zijn nog even gesloten in afwachting van het voltooien van de"
               " werken. Tot dan kan je's middags en 's avonds terecht in Resto Kantienberg. Wij houden jullie op de"
               " hoogte!<br>'s Middags is Resto Sint-Jansvest tijdelijk een reguliere resto met een uitgebreid aanbod"
               " aan belegde broodjes. Enkel soep of broodjes nodig? Dan is Cafetaria campus Boekentoren (via"
               " Blandijnberg) zeer dichtbij.")
    return {
        "message": message,
        "date": original["date"],
        "open": False
    }


def tijdelijke_sluiting_sint_jansvest(_path, original):
    message = "Resto Sint-Jansvest is tijdelijk gesloten wegens wegenwerken. Tijdens de werken kan u terecht in De " \
              "Brug. "
    return {
        "message": message,
        "date": original["date"],
        "open": False,
        "meals": original.get("meals", [])
    }


def corona_sluiting_nl(_path, original):
    message = "De studentenrestaurants en cafetaria's sluiten vanaf maandag 16 maart 2020 de deuren. " \
              "De UGent neemt die maatregel om verdere verspreiding van het coronavirus tot een minimum te beperken. " \
              "De sluiting loopt zeker tot en met 7 juni 2020."
    return {
        "message": message,
        "date": original["date"],
        "open": False
    }


def corona_sluiting_en(_path, original):
    message = "The student restaurants and cafeterias will be closed as from Monday 16 March 2020. " \
              "Ghent University is taking this measure to minimize the further spreading of the coronavirus. " \
              "The closure will certainly last until 7 June 2020."
    return {
        "message": message,
        "date": original["date"],
        "open": False
    }


def corona_heropening_nl(_path, original):
    message = "Ter plaatse eten is momenteel niet mogelijk; enkel takeaway van een beperkt aanbod. De coronamaatregelen blijven van kracht! " \
              "Resto Dunant, Coupure en Sterre en van cafetaria UZ Gent en Boekentoren zijn opnieuw open. " \
              "Bij de start van het academiejaar volgen de andere locaties."
    return {
        "message": message,
        "date": original["date"],
        "open": True,
        "meals": [{
            "kind": "meat",
            "type": "main",
            "name": "Spaghetti bolognese met kaas",
            "price": "\u20ac 3,60"
        }, {
            "kind": "vegetarian",
            "type": "main",
            "name": "Salad bowl: Caesar",
            "price": ""
        }, {
            "kind": "vegetarian",
            "type": "main",
            "name": "Salad bowl: Tomaat-Mozzarella",
            "price": ""
        }, {
            "kind": "soup",
            "type": "main",
            "name": "Dagsoep",
            "price": ""
        }],
        "vegetables": []
    }


def corona_heropening_en(_path, original):
    message = "The canteen is closed; only takeaway of a reduced offering is possible. The Corona measures remain active! " \
              "Resto Dunant, Coupure & Sterre and cafetaria UZ Gent & Boekentoren are open. " \
              "At the start of the academic year, the other locations will follow."
    return {
        "message": message,
        "date": original["date"],
        "open": True,
        "meals": [{
            "kind": "meat",
            "type": "main",
            "name": "Spaghetti bolognese with cheese",
            "price": "\u20ac 3,60"
        }, {
            "kind": "vegetarian",
            "type": "main",
            "name": "Salad bowl: Caesar",
            "price": ""
        }, {
            "kind": "vegetarian",
            "type": "main",
            "name": "Salad bowl: Tomato-Mozzarella",
            "price": ""
        }, {
            "kind": "soup",
            "type": "main",
            "name": "Soup of the day",
            "price": ""
        }],
        "vegetables": []
    }


def corona_closed_for_now(_path, original):
    message = "Resto Dunant, Coupure en Sterre en van cafetaria UZ Gent en Boekentoren zijn opnieuw open. " \
              "Bij de start van het academiejaar volgen de andere locaties."
    return {
        "message": message,
        "date": original["date"],
        "open": False
    }


def kantienberg_2020(_path, original):
    return {
        "message": "Resto Kantienberg blijft gesloten tijdens academiejaar 2020-2021.",
        "date": original["date"],
        "open": False
    }


def corona_2020_2021_nl(_path, original):
    message = "Door de coronamaatregelen veranderen enkele zaken: ter plaatse eten is niet mogelijk " \
              "(enkel afhalen) en er is een beperkter aanbod."
    original["message"] = message
    return original


def corona_2020_2021_en(_path, original):
    message = "Due to the corona measures, some changes are made: only takeaway is possible " \
              "and the offering is reduced."
    original["message"] = message
    return original


def corona_2020_2021_nl_red(_path, original):
    message = "Enkel afhalen en een beperkter aanbod. De coronamaatregelen blijven van kracht!"
    original["message"] = message
    return original


def corona_2020_2021_cold(_path, original):
    message = "Enkel cafetaria-aanbod en koude meeneemgerechten. De coronamaatregelen blijven van kracht!"
    original["message"] = message
    return original


def corona_2020_2021_en_red(_path, original):
    message = "Due to the corona measures, some changes are made: only takeaway is possible " \
              "and the offering is reduced. " \
              "The restaurants and cafetaria's will remain open in code red."
    original["message"] = message
    return original


def exam_closure_sterre_2020(_path, original):
    message = "Door examens zal de resto gesloten zijn op 4, 15, 18 en 26 januari."
    original["message"] = message
    original["open"] = False
    return original


def exam_closure_dunant_2020(_path, original):
    message = "Door examens zal de resto gesloten zijn op 4, 8, 15, 18, 22, 25 en 29 januari."
    original["message"] = message
    original["open"] = False
    return original


def christmas(_path, original):
    original["message"] = "Naast de UGent-verlofdagen zijn de resto's ook gesloten tijdens de eerste week van de " \
                          "kerstvakantie. "
    original["open"] = False
    return original


def exam_closure_en_2020(_path, original):
    original["message"] = "Resto Sterre and Dunant are closed on some days in January due to exams. Check the site " \
                          "for more details."
    return original


def dies_natalis_2021(_path, original):
    original["message"] = "De resto's zijn gesloten op Dies Natalis."
    original["open"] = False
    return original


def dies_natalis_2021_en(_path, original):
    original["message"] = "The restaurants are closed on Dies Natalis."
    original["open"] = False
    return original


def easter_2021_week1(_path, original):
    original["message"] = "In de paasvakantie zullen resto's Sterre, Ardoyen, De Brug en UZ Gent open zijn, " \
                          "maar enkel als cafetaria. "
    original["open"] = True
    return original


def easter_2021_week2(_path, original):
    original["message"] = "In de paasvakantie zullen resto's Sterre, Ardoyen, De Brug, UZ Gent en Coupure open zijn, " \
                          "maar enkel als cafetaria. "
    original["open"] = True
    return original

def summer_2021_1(_path, original):
    original["message"] = "Cafetaria de Brug en resto's Ardoyen, Sterre en Merelbeke met een gewijzigd aanbod. Er zullen" \
                          " dan enkel broodjes en salad bowls te verkrijgen zijn. De zitplaatsen kunnen nog niet gebruikt worden."
    original["open"] = True
    return original

def summer_2021_2(_path, original):
    original["message"] = "Cafetaria's de Brug en UZ Gent, en resto's Ardoyen, Sterre, Coupure en Merelbeke met een gewijzigd aanbod. Er zullen" \
                          " dan enkel broodjes en salad bowls te verkrijgen zijn. De zitplaatsen kunnen nog niet gebruikt worden."
    original["open"] = True
    return original

def brug_avond(_path, original):
    original["message"] = "De Brug is vrijdagavond gesloten."
    return original

def november_12_2021(_path, original):
    original["message"] = "Vrijdag 12 november zullen alle resto's en cafetaria's gesloten zijn, behalve cafetaria De Brug."
    original["open"] = False
    return original

def november_12_2021_en(_path, original):
    original["message"] = "Friday, the 12th of November, all restos and cafeterias will be closed except for cafeteria De Brug."
    original["open"] = False
    return original

def heymans_november_22_2021(_path, original):
    original["message"] = "Maandag 22 en dinsdag 23 november is Cafetaria Heymans uitzonderlijk gesloten."
    original["open"] = True
    return original

def heymans_november_22_2021_en(_path, original):
    original["message"] = "Monday, the 22th and Tuesday, the 23th of November, Cafetaria Heymans is exceptionally closed."
    original["open"] = True
    return original

def heymans_november_23_2021(_path, original):
    original["message"] = "Cafetaria Heymans terug open op 23 november."
    original["open"] = True
    return original

def heymans_november_23_2021_en(_path, original):
    original["message"] = "Cafetaria Heymans open again on 23th of November."
    original["open"] = True
    return original

def heymans_november_24_26_2021(_path, original):
    original["message"] = "Cafetaria Heymans is gesloten op 24, 25 en 26 november. Cafetaria UZ Gent is open."
    original["open"] = True
    return original

def heymans_november_24_26_2021_en(_path, original):
    original["message"] = "Cafetaria Heymans will be closed on 24, 25 and 26 November. Cafeteria UZ Gent is open."
    original["open"] = True
    return original

def christmas_2021(_path, original):
    original["message"] = "De Brug Avond, cafetaria’s Boekentoren, Ledeganck en Heymans gesloten vanaf 20 december. Alle resto’s en cafetaria’s gesloten op 23 en 24 december en op 3 januari."
    original["open"] = True
    return original

def christmas_2021_en(_path, original):
    original["message"] = "De Brug Evening, cafeterias Boekentoren, Ledeganck and Heymans closed as of December 20. All restos and cafeterias closed on December 23 and 24 and on January 3."
    original["open"] = True
    return original


def newyear_2022(_path, original):
    original["message"] = "Van 4 t.e.m. 7 januari zijn enkel Resto De Brug, Resto Sterre, Resto Coupure, Resto Ardoyen en Cafetaria UZ Gent open. Enkel in Resto De Brug zijn er warme maaltijden."
    original["open"] = True
    return original


def newyear_2022_en(_path, original):
    original["message"] = "From 4 to 7 January only Resto De Brug, Resto Sterre, Resto Coupure, Resto Ardoyen and Cafetaria UZ Gent will be open. Only in Resto De Brug there are warm meals."
    original["open"] = True
    return original


def closures_january_2022(_path, original):
    original["message"] = "Cafetaria’s Boekentoren en Ledeganck gesloten, geen warme maaltijden meer in resto’s Dunant en Merelbeke."
    original["open"] = True
    return original


def closures_january_2022_en(_path, original):
    original["message"] = "Cafeterias Boekentoren and Ledeganck closed, no more warm meals in restaurants Dunant and Merelbeke."
    original["open"] = True
    return original


def paasvakantie2022(_path, original):
    original["message"] = "In de paasvakantie wijzigt de dienstverlening grondig. " \
                          "Warme maaltijden enkel in De Brug, uitgezonderd de sluiting op 8 en 15 april. " \
                          "Bekijk de website voor alle details over alle locaties."
    return original


def easter2022(_path, original):
    original["message"] = "In the easter recess, the service is heavily modified. " \
                          "Hot meals only in the Brug, except the closure on April 8th and April 15th. " \
                          "Check the website for more details on all locations."
    return original


def zomer_2022_1(_path, original):
    original["message"] = "In juli, augustus en september sluiten verschillende resto's of doen ze enkel dienst als cafetaria. " \
                          "Kijk op de website voor alle details."
    return original


def summer_2022_1(_path, original):
    original["message"] = "In July, August and September, multiple restaurants close or only act as a cafetaria. " \
                          "Check the website for more details."
    return original


def zomer_2022_2(_path, original):
    original["message"] = "Vanaf 18 juli tot en met 29 juli zijn alle resto's en cafetaria's gesloten."
    original["open"] = False
    return original


def summer_2022_2(_path, original):
    original["message"] = "From July 18th until July 29th, all restaurants and cafeterias are closed."
    original["open"] = False
    return original


def close_time_nl(_path, original):
    if "message" in original:
        original["message"] += " Op 20 september zijn alle resto’s en cafetaria’s gesloten door onze teambuilding."
    else:
        original["message"] = "Op 20 september zijn alle resto’s en cafetaria’s gesloten door onze teambuilding."
    original["open"] = False
    return original


def close_time_en(_path, original):
    if "message" in original:
        original["message"] += " All restaurants and cafeterias are closed on 20 September, due to our team building."
    else:
        original["message"] = "All restaurants and cafeterias are closed on 20 September, due to our team building."
    original["open"] = False
    return original


def close_ardoyen_nl(_path, original):
    if "message" in original:
        original["message"] += " Op 16 september is Resto Ardoyen gesloten wegens het openingsevent van het FSVM2 onderzoeksgebouw."
    else:
        original["message"] = "Op 16 september is Resto Ardoyen gesloten wegens het openingsevent van het FSVM2 onderzoeksgebouw."
    return original


def close_ardoyen_en(_path, original):
    if "message" in original:
        original["message"] += " Resto Ardoyen is closed on 16 September, due to the opening event of the FSVM2 research building."
    else:
        original["message"] = "Resto Ardoyen is closed on 16 September, due to the opening event of the FSVM2 research building."
    return original


def no_more_soup_nl(_path, original):
    original["message"] = "Door ernstige productieproblemen bij de leverancier is er tijdelijk geen soep meer te " \
                          "verkrijgen. We werken hard aan een oplossing en vanaf 3 november zal er opnieuw " \
                          "soep zijn. Hou onze website en de TV-schermen in de gaten voor de meest recente update " \
                          "hierover. "
    return original


def no_more_soup_en(_path, original):
    original["message"] = "Due to serious production problems at the purveyor, soup will temporarily no longer be " \
                          "available. We are working hard to resolve this issue. Soup will be available again " \
                          "November 3th. Watch our website and tv screens for the most up-to-date " \
                          "information. "
    return original


def strike_nl(_path, original):
    original["message"] = "Opgelet: op woensdag 9 november kan de dienstverlening verstoord zijn door een " \
                          "nationale stakingsactie. Wij zullen 's ochtends pas weten welke resto's en cafetaria's" \
                          "open kunnen gaan en welk aanbod er zal zijn."
    return original


def strike_en(_path, original):
    original["message"] = "On Wednesday November 9th our services may be interrupted due to a national strike." \
                          "We will only know in the morning which restaurants and/or cafeterias wil " \
                          "be open and what their offer will be."
    return original


def leak_nl(_path, original):
    original["message"] = "Deze week is cafetaria Heymans gesloten wegens een waterlek."
    return original


def leak_en(_path, original):
    original["message"] = "Cafetaria Heymans is closed this week due to a water leak."
    return original


def winter_2022_nl(_path, original):
    original["message"] = "Van 23/12 tot 2/01 sluiten de resto's. Sommige resto's of cafetaria's sluiten vroeger. " \
                          "In resto Merelbeke zijn geen warme maaltijden tot en met 6 januari."
    return original


def winter_2022_en(_path, original):
    original["message"] = "From 23/12 until 2/01 de resto's are closed. Some locations close earlier. " \
                          "In resto Merelbeke there are no hot meals until January 6th."
    return original


def create_changes(root_path):
    return [
        # Restjesmaand 2018
        ManualChange(
            replacer=restjesmaand18_replacer,
            resto="nl-sintjansvest",
            start=date(2018, 6, 1),
            end=date(2018, 6, 30),
        ),
        # Dingen voor de paasvakantie 19
        ManualChange(
            replacer=paasvakantie19_general,
            resto="nl",
            start=date(2019, 4, 8),
            end=date(2019, 4, 19)
        ),
        ManualChange(
            replacer=paasvakantie19_en,
            resto="en",
            start=date(2019, 4, 8),
            end=date(2019, 4, 19)
        ),
        ManualChange(
            replacer=paasvakantie19_brug,
            resto="nl-debrug",
            start=date(2019, 4, 8),
            end=date(2019, 4, 19)
        ),
        # Werken aan De Brug from 20/05/2019 - 30/09/2019
        ManualChange(
            replacer=werken_brug19_replacer,
            resto="nl-debrug",
            start=date(2019, 5, 20),
            end=date(2019, 9, 29),
            all_days=True
        ),
        # Er is nog meer vertraging
        ManualChange(
            replacer=werken_brug19_replacer2,
            resto="nl-debrug",
            start=date(2019, 9, 30),
            end=date(2019, 11, 11),
            all_days=True
        ),
        ManualChange(
            replacer=tijdelijke_sluiting_sint_jansvest,
            resto="nl-sintjansvest",
            start=date(2019, 12, 16),
            end=date(2020, 1, 10),
            all_days=True,
        ),
        # Corona
        ManualChange(
            replacer=corona_sluiting_nl,
            resto=["nl", "nl-sintjansvest", "nl-debrug", "nl-heymans", "nl-kantienberg"],
            start=date(2020, 3, 16),
            end=date(2020, 6, 7),
            all_days=True
        ),
        ManualChange(
            replacer=corona_sluiting_en,
            resto="en",
            start=date(2020, 3, 16),
            end=date(2020, 6, 7),
            all_days=True
        ),
        ManualChange(
            replacer=corona_heropening_nl,
            resto="nl",
            start=date(2020, 9, 7),
            end=date(2020, 9, 20),
            all_days=True
        ),
        ManualChange(
            replacer=corona_heropening_en,
            resto="en",
            start=date(2020, 9, 7),
            end=date(2020, 9, 20),
            all_days=True
        ),
        ManualChange(
            replacer=corona_closed_for_now,
            resto=["nl-debrug", "nl-heymans"],
            start=date(2020, 9, 7),
            end=date(2020, 9, 20),
            all_days=True
        ),
        ManualChange(
            replacer=kantienberg_2020,
            resto="nl-kantienberg",
            start=date(2020, 9, 7),
            end=date(2021, 7, 1),
            all_days=True
        ),
        ManualChange(
            replacer=corona_2020_2021_en,
            resto="en",
            start=date(2020, 9, 21),
            end=date(2020, 10, 18)
        ),
        ManualChange(
            replacer=corona_2020_2021_nl,
            resto=["nl", "nl-debrug", "nl-heymans"],
            start=date(2020, 9, 21),
            end=date(2020, 10, 18)
        ),
        ManualChange(
            replacer=corona_2020_2021_en_red,
            resto="en",
            start=date(2020, 10, 19),
            end=date(2020, 12, 19)
        ),
        ManualChange(
            replacer=corona_2020_2021_nl_red,
            resto=["nl-debrug", "nl-heymans", "nl-sterre", "nl-ardoyen"],
            start=date(2020, 10, 19),
            end=date(2020, 12, 19)
        ),
        ManualChange(
            replacer=corona_2020_2021_cold,
            resto=["nl-coupure", "nl-dunant", "nl-merelbeke"],
            start=date(2020, 11, 28),
            end=date(2020, 12, 31)
        ),
        ManualChange(
            replacer=christmas,
            resto=["nl-debrug", "nl-heymans", "nl-dunant", "nl-coupure", "nl-sterre", "nl-ardoyen", "nl-merelbeke"],
            start=date(2020, 12, 21),
            end=date(2020, 12, 25),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_dunant_2020,
            resto="nl-dunant",
            start=date(2021, 1, 4),
            end=date(2021, 1, 4),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_dunant_2020,
            resto="nl-dunant",
            start=date(2021, 1, 8),
            end=date(2021, 1, 8),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_dunant_2020,
            resto="nl-dunant",
            start=date(2021, 1, 15),
            end=date(2021, 1, 15),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_dunant_2020,
            resto="nl-dunant",
            start=date(2021, 1, 18),
            end=date(2021, 1, 18),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_dunant_2020,
            resto="nl-dunant",
            start=date(2021, 1, 22),
            end=date(2021, 1, 22),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_dunant_2020,
            resto="nl-dunant",
            start=date(2021, 1, 25),
            end=date(2021, 1, 25),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_dunant_2020,
            resto="nl-dunant",
            start=date(2021, 1, 29),
            end=date(2021, 1, 29),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_sterre_2020,
            resto="nl-sterre",
            start=date(2021, 1, 4),
            end=date(2021, 1, 5),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_sterre_2020,
            resto="nl-sterre",
            start=date(2021, 1, 4),
            end=date(2021, 1, 4),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_sterre_2020,
            resto="nl-sterre",
            start=date(2021, 1, 15),
            end=date(2021, 1, 15),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_sterre_2020,
            resto="nl-sterre",
            start=date(2021, 1, 18),
            end=date(2021, 1, 18),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_sterre_2020,
            resto="nl-sterre",
            start=date(2021, 1, 26),
            end=date(2021, 1, 26),
            all_days=True
        ),
        ManualChange(
            replacer=exam_closure_en_2020,
            resto="en",
            start=date(2021, 1, 4),
            end=date(2021, 1, 29),
            all_days=False
        ),
        ManualChange(
            replacer=dies_natalis_2021,
            resto=["nl-debrug", "nl-heymans", "nl-dunant", "nl-coupure", "nl-sterre", "nl-ardoyen", "nl-merelbeke"],
            start=date(2021, 3, 19),
            end=date(2021, 3, 19),
            all_days=True
        ),
        ManualChange(
            replacer=dies_natalis_2021_en,
            resto="en",
            start=date(2021, 3, 19),
            end=date(2021, 3, 19),
            all_days=True
        ),
        ManualChange(
            replacer=easter_2021_week1,
            resto=["nl-debrug", "nl-heymans", "nl-sterre", "nl-ardoyen"],
            start=date(2021, 4, 5),
            end=date(2021, 4, 9),
            all_days=True
        ),
        ManualChange(
            replacer=easter_2021_week2,
            resto=["nl-debrug", "nl-heymans", "nl-sterre", "nl-ardoyen", "nl-coupure"],
            start=date(2021, 4, 12),
            end=date(2021, 4, 16),
            all_days=True
        ),
        ManualChange(
            replacer=summer_2021_1,
            resto=["nl-debrug", "nl-sterre", "nl-ardoyen", "nl-merelbeke"],
            start=date(2021, 8, 9),
            end=date(2021, 4, 16),
            all_days=True
        ),
        ManualChange(
            replacer=summer_2021_2,
            resto=["nl-sterre", "nl-merelbeke", "nl-coupure", "nl-heymans"],
            start=date(2021, 8, 16),
            end=date(2021, 9, 13),
            all_days=True
        ),
        ManualChange(
            replacer=summer_2021_2,
            resto="nl-debrug",
            start=date(2021, 8, 16),
            end=date(2021, 9, 1),
            all_days=True
        ),
        ManualChange(
            replacer=summer_2021_2,
            resto="nl-ardoyen",
            start=date(2021, 8, 16),
            end=date(2021, 8, 25),
            all_days=True
        ),
        *[ManualChange(
            replacer=brug_avond,
            resto="nl",
            start=date(2021, 11, 22) + timedelta(days=x),
            end=date(2021, 11, 22) + timedelta(days=x)
        ) for x in range((date(2021, 12, 31) - date(2021, 11, 22)).days + 1) if
            (date(2021, 11, 22) + timedelta(days=x)).weekday() == 4],
        ManualChange(
            replacer=november_12_2021,
            resto=["nl"],
            start=date(2021, 11, 12),
            end=date(2021, 11, 12),
            all_days=True
        ),
        ManualChange(
            replacer=november_12_2021_en,
            resto=["en"],
            start=date(2021, 11, 12),
            end=date(2021, 11, 12),
            all_days=True
        ),
        ManualChange(
            replacer=heymans_november_22_2021,
            resto=["nl"],
            start=date(2021, 11, 22),
            end=date(2021, 11, 22),
            all_days=True
        ),
        ManualChange(
            replacer=heymans_november_22_2021_en,
            resto=["en"],
            start=date(2021, 11, 22),
            end=date(2021, 11, 22),
            all_days=True
        ),
        ManualChange(
            replacer=heymans_november_23_2021,
            resto=["nl"],
            start=date(2021, 11, 23),
            end=date(2021, 11, 23),
            all_days=True
        ),
        ManualChange(
            replacer=heymans_november_23_2021_en,
            resto=["en"],
            start=date(2021, 11, 23),
            end=date(2021, 11, 23),
            all_days=True
        ),
        ManualChange(
            replacer=heymans_november_24_26_2021,
            resto=["nl"],
            start=date(2021, 11, 24),
            end=date(2021, 11, 26),
            all_days=True
        ),
        ManualChange(
            replacer=heymans_november_24_26_2021_en,
            resto=["en"],
            start=date(2021, 11, 24),
            end=date(2021, 11, 26),
            all_days=True
        ),
        ManualChange(
            replacer=christmas_2021,
            resto=["nl"],
            start=date(2021, 12, 20),
            end=date(2022, 1, 3),
            all_days=True
        ),
        ManualChange(
            replacer=christmas_2021_en,
            resto=["en"],
            start=date(2021, 12, 20),
            end=date(2022, 1, 3),
            all_days=True
        ),
        ManualChange(
            replacer=newyear_2022,
            resto=["nl"],
            start=date(2022, 1, 4),
            end=date(2022, 1, 7),
            all_days=True
        ),
        ManualChange(
            replacer=newyear_2022_en,
            resto=["en"],
            start=date(2022, 1, 4),
            end=date(2022, 1, 7),
            all_days=True
        ),
        ManualChange(
            replacer=closures_january_2022,
            resto=["nl"],
            start=date(2022, 1, 17),
            end=date(2022, 1, 28),
            all_days=True
        ),
        ManualChange(
            replacer=closures_january_2022_en,
            resto=["en"],
            start=date(2022, 1, 17),
            end=date(2022, 1, 28),
            all_days=True
        ),
        ManualChange(
            replacer=paasvakantie2022,
            resto=["nl"],
            start=date(2022, 4, 4),
            end=date(2022, 4, 17),
            all_days=True
        ),
        ManualChange(
            replacer=easter2022,
            resto=["en"],
            start=date(2022, 4, 4),
            end=date(2022, 4, 17),
            all_days=True
        ),
        ManualChange(
            replacer=zomer_2022_1,
            resto=["nl"],
            start=date(2022, 6, 27),
            end=date(2022, 7, 15),
            all_days=True
        ),
        ManualChange(
            replacer=summer_2022_1,
            resto=["en"],
            start=date(2022, 6, 27),
            end=date(2022, 7, 15),
            all_days=True
        ),
        ManualChange(
            replacer=zomer_2022_2,
            resto=["nl"],
            start=date(2022, 7, 18),
            end=date(2022, 7, 29),
            all_days=True
        ),
        ManualChange(
            replacer=summer_2022_2,
            resto=["en"],
            start=date(2022, 7, 18),
            end=date(2022, 7, 29),
            all_days=True
        ),
        ManualChange(
            replacer=zomer_2022_1,
            resto=["nl"],
            start=date(2022, 8, 1),
            end=date(2022, 9, 16),
            all_days=True
        ),
        ManualChange(
            replacer=summer_2022_1,
            resto=["en"],
            start=date(2022, 8, 1),
            end=date(2022, 9, 16),
            all_days=True
        ),
        ManualChange(
            replacer=close_time_nl,
            resto=["nl"],
            start=date(2022, 9, 14),
            end=date(2022, 9, 20),
            all_days=True
        ),
        ManualChange(
            replacer=close_time_en,
            resto=["en"],
            start=date(2022, 9, 14),
            end=date(2022, 9, 20),
            all_days=True
        ),
        ManualChange(
            replacer=close_ardoyen_nl,
            resto=["nl"],
            start=date(2022, 9, 15),
            end=date(2022, 9, 16),
            all_days=True
        ),
        ManualChange(
            replacer=close_ardoyen_en,
            resto=["en"],
            start=date(2022, 9, 15),
            end=date(2022, 9, 16),
            all_days=True
        ),
        ManualChange(
            replacer=no_more_soup_nl,
            resto=["nl"],
            start=date(2022, 10, 26),
            end=date(2022, 11, 2),
            all_days=True
        ),
        ManualChange(
            replacer=no_more_soup_en,
            resto=["en"],
            start=date(2022, 10, 26),
            end=date(2022, 11, 2),
            all_days=True
        ),
        ManualChange(
            replacer=strike_nl,
            resto=["nl"],
            start=date(2022, 11, 7),
            end=date(2022, 11, 9),
            all_days=True
        ),
        ManualChange(
            replacer=strike_en,
            resto=["en"],
            start=date(2022, 11, 7),
            end=date(2022, 11, 9),
            all_days=True
        ),
        ManualChange(
            replacer=leak_nl,
            resto=["nl"],
            start=date(2022, 11, 15),
            end=date(2022, 11, 19),
            all_days=True
        ),
        ManualChange(
            replacer=leak_en,
            resto=["en"],
            start=date(2022, 11, 15),
            end=date(2022, 11, 19),
            all_days=True
        ),
        ManualChange(
            replacer=winter_2022_nl,
            resto=["nl"],
            start=date(2022, 12, 8),
            end=date(2023, 1, 6),
            all_days=True
        ),
        ManualChange(
            replacer=winter_2022_en,
            resto=["en"],
            start=date(2022, 12, 8),
            end=date(2023, 1, 6),
            all_days=True
        )
    ]


# Actually do things ----------------------------------------------------------

def apply_existing_menus_only(output, manual_change, dates):
    """Apply the change to only existing menus"""
    print(f"Matching existing menus from {manual_change.resto} between {manual_change.start} to {manual_change.end}")
    print("====================================================================")

    for resto in manual_change.resto:
        files = glob.glob(f"{output}/menu/{resto}/*/*/*.json")
        file_pattern = re.compile(r'.*/(\d+)/(\d+)/(\d+)\.json$')
        for path in files:
            # Check if this file applies or not.
            m = file_pattern.search(path.replace("\\", "/"))
            file_date = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if not manual_change.is_applicable(file_date):
                continue

            with open(path, 'r') as f:
                overview = json.loads(f.read())
                _new_content = manual_change.replacer(path, overview)
                dates[resto][_new_content["date"]] = _new_content
                new_content = json.dumps(_new_content)

            with open(path, 'w') as f:
                f.write(new_content)


def apply_all_menus(output, manual_change, dates):
    """Apply the change to all dates in the applicable range. If no menu exist for a day, it will be created."""
    print(f"Matching all menus from {manual_change.resto} between {manual_change.start} to {manual_change.end}")
    print("====================================================================")

    for applicable_date in manual_change.date_range():
        year = applicable_date.year
        month = applicable_date.month
        day = applicable_date.day
        # Get existing file if it exists
        for resto in manual_change.resto:
            path = f"{output}/menu/{resto}/{year}/{month}/{day}.json"
            try:
                with open(path, 'r') as f:
                    menu = json.loads(f.read())
            except IOError:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                menu = {'open': False, 'date': applicable_date.strftime('%Y-%m-%d'), 'meals': [], 'vegetables': []}

            # Apply the changes
            _new_content = manual_change.replacer(path, menu)
            dates[resto][_new_content["date"]] = _new_content
            new_content = json.dumps(_new_content)

            with open(path, 'w+') as f:
                f.write(new_content)


def main(output):
    to_apply = create_changes(output)

    dates = defaultdict(dict)
    for manual_change in to_apply:
        if manual_change.all_days:
            apply_all_menus(output, manual_change, dates)
        else:
            apply_existing_menus_only(output, manual_change, dates)

    for manual_change in to_apply:
        print("Rebuilding overviews")
        for resto in manual_change.resto:
            match_glob = f"menu/{resto}/overview.json"
            print(match_glob)
            overviews = glob.glob(f"{output}/{match_glob}")

            # For each overview that should be rebuild
            for path in overviews:
                print(f"Rebuilding {path}")
                new_overview = []
                with open(path, 'r') as f:
                    overview = json.loads(f.read())

                last_day = None
                # If the date is modified, replace it
                for day in overview:
                    if day["date"] in dates[resto]:
                        print(f"Updating {day['date']}")
                        new_overview.append(dates[resto][day["date"]])
                    else:
                        print(f"Keeping {day['date']}")
                        new_overview.append(day)
                    last_day = day["date"]

                # We want to provide at least ten days in the future.
                to_add = max(OVERVIEW_COUNT - len(overview), 0)
                if last_day:
                    last_day = datetime.strptime(last_day, '%Y-%m-%d').date()
                for day in dates[resto]:
                    dday = datetime.strptime(day, '%Y-%m-%d').date()
                    if ((last_day and dday <= last_day) or (last_day is None and dday < date.today())) or to_add <= 0:
                        continue
                    new_overview.append(dates[resto][day])
                    to_add -= 1

                with open(path, 'w') as f:
                    f.write(json.dumps(new_overview))
                    print("Wrote updated overview")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Apply manual corrections to scraped menu')
    parser.add_argument('output', help='Folder of v2 output.')
    args = parser.parse_args()

    main(args.output)
