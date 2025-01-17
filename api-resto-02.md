# Resto API 2.X

## Introduction

The resto API provides information about the student restaurants of Ghent University.

These data are scraped from https://www.ugent.be/student/nl/meer-dan-studeren/resto.

The menu data is property of Ghent University. We don't guarantee the correctness or completeness of the data.

## Versioning and status

This document describes the current version of the API, version 2.0.

| Version                | Endpoint                              | Status  |
|------------------------|---------------------------------------|---------|
| [1.0](api-resto-01.md) | https://hydra.ugent.be/api/1.0/resto/ | retired |
| 2.4 (this)             | https://hydra.ugent.be/api/2.0/resto/ | current |

## Data dump

All scraped data available in this API is also available as a [git repository](https://git.zeus.gent/hydra/data). If you
need all available data, it is probably easier and faster to download or clone the repo.

## Changelog

- _April 2019_ - Added new `message` field to the menu to indicate closures and changes in meals. (2.1)
- _September 2019_ - Added ecological sandwich of the week (2.2)
- _September 2020_ - Corona update (2.3):
    - The meal type `side` is no longer used.
    - A new meal type is present: `cold`.
    - Add a new endpoint for salad bowls.
    - API 1.0 has been retired.
- At some point in 2021 or early 2022, the zeus.ugent.be/hydra endpoint stopped working. We could fix it, but we assume
  most clients have migrated or are able to.
- _October 2022_ - Allergen information was added.

## Technical description

| Endpoint                                                       | Description                                                        |
|----------------------------------------------------------------|--------------------------------------------------------------------|
| [`GET /meta.json`](#metadata)                                  | Information about the resto's.                                     |
| [`GET /extrafood.json`](#extra-food)                           | List of additional available items, such as breakfast or desserts. |
| [`GET /menu/{endpoint}/overview.json`](#overview-menu)         | The future menu for a specific resto.                              |
| [`GET /menu/{endpoint}/{year}/{month}/{day}.json`](#day-menu)  | The menu for a particular day.                                     |
| `GET /sandwiches.json`                                         | (deprecated)                                                       |
| [`GET /sandwiches/static.json`](#regular-sandwiches)           | List of normal sandwiches.                                         |
| [`GET /sandwiches/overview.json`](#weekly-sandwiches-overview) | Upcoming ecological sandwiches.                                    |
| [`GET /sandwiches/{year}.json`](#weekly-sandwiches-yearly)     | All ecological sandwiches.                                         |
| [`GET /salads.json`](#salad-bowls)                             | Available salad bowls                                              |
| [`GET /allergens.json`](#allergen-information)                 | Allergen information                                               |

Date and hour specifiers are from ISO 8601:2014.

### Metadata

**Endpoint**: `GET /meta.json`

The main entry point for the API. Provides a list of all locations known to the API. This data is manually curated;
please raise an issue if data is missing or incorrect.
Example response:

```json
{
 "locations": [
  {
   "name": "Resto Campus Sterre",
   "address": "Krijgslaan 281",
   "latitude": 51.026024,
   "longitude": 3.712939,
   "type": "resto",
   "endpoint": "nl",
   "open": {
    "resto": [
     [
      "11:15",
      "14:00"
     ]
    ],
    "cafetaria": [
     [
      "08:00",
      "14:00"
     ]
    ]
   }
  }
 ]
}
```

The response is an object with one field, `locations`, a list of locations.

| Field                   | Description                                                                                                                                                                                                                                                  |
|-------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `name`                  | Name of the location.                                                                                                                                                                                                                                        |
| `address`               | Address of the location.                                                                                                                                                                                                                                     |
| `latitude`, `longitude` | Coordinates of the location.                                                                                                                                                                                                                                 |
| `type`                  | The main type of the resto. For example, `resto` indicates it is a resto, but it might also be a cafetaria.                                                                                                                                                  |
| `endpoint`              | The endpoint for this resto. Can be used in `/resto/menu/{ENDPOINT}`. See [Overview](#overview-menu) or [Day menu](#day-menu).                                                                                                                               |
| `open`                  | Lists the intervals in which this location is open, for each type of the location. Uses ISO 8601:2014's extended format with reduced accuracy (`hh:mm`). These are the regular opening hours; holidays and other exceptional closures are not accounted for. |

### Extra food

**Endpoint**: `GET /extrafood.json`

Returns additional items that may be available. The actual availability varies per location, but this information is not
known in the API. Sample output:

```json
{
 "breakfast": [
  {
   "name": "Croissant",
   "price": "0.80"
  }
 ],
 "desserts": [
  {
   "name": "Vruchtenyoghurt",
   "price": "0.70"
  }
 ],
 "drinks": [
  {
   "name": "Plat water 1l",
   "price": "1.20"
  }
 ]
}
```

There are three lists in the response: `breakfast`, `desserts` and `drinks`. Each item in a list consists of a `name`and
a `price` in euros (textual).

_Note_: the price format is not identical as the price format used by the [Day Menu](#day-menu) output.

### Overview menu

**Endpoint**: `GET \menu\{endpoint}\overview.json`

**Parameters**:

- _endpoint_ -- The endpoint for the resto. Available endpoint can be queried using the [Metadata](#metadata) request.

Returns the menu for each available day in the future, including today. Sample output:

```json
[
 {
  "date": "2018-03-05",
  "meals": [
   {
    "kind": "soup",
    "name": "Minestrone",
    "price": "€ 0,50",
    "type": "side"
   },
   {
    "kind": "meat",
    "name": "Keftaballetjes in tomatensaus",
    "price": "€ 3,90",
    "type": "main",
    "allergens": []
   },
   {
    "kind": "fish",
    "name": "Alaska pollak italiano",
    "price": "€ 3,60",
    "type": "main",
    "allergens": [
     "selderij"
    ]
   },
   {
    "kind": "vegetarian",
    "name": "Moussaka met seitan",
    "price": "€ 4,70",
    "type": "main",
    "allergens": [
     "selderij"
    ]
   }
  ],
  "open": true,
  "vegetables": [
   "Bloemkool",
   "Prinsessengroenten"
  ],
  "message": "Alle studenten krijgen op vertoon van Hydra 150% korting."
 }
]
```

The output consists of an array, with a menu object for each day. See [Day Menu](#day-menu) for a description.

### Day Menu

**Endpoint**: `GET /menu/{endpoint}/{year}/{month}/{day}.json`

**Parameters**:

Date formatters in this section are from ISO 8601:2014. Dates are basically ISO, but without leading zeroes.

- _endpoint_ — The endpoint for the resto. Available endpoint can be queried using the [Metadata](#metadata) request.
- _year_ — The year of the date. Values must be a positive integer. Currently, the earliest available year is 2016 (but
  this might change in the future). ISO format: `Y̲Y`.
- _month_ — The month of the date. Values must be in the interval [1-12], and formatted without leading zeroes. ISO
  format: `M̲M`
- _day_ — The day of the date. Values must be in the interval [1-31], and formatted without leading zeroes. ISO
  format: `D̲D`.

A sample endpoint is `/menu/nl/2017/5/18.json`. Sample output is:

```json
{
 "date": "2018-03-05",
 "meals": [
  {
   "kind": "soup",
   "name": "Minestrone",
   "price": "€ 0,50",
   "type": "side",
   "allergens": []
  },
  {
   "kind": "meat",
   "name": "Keftaballetjes in tomatensaus",
   "price": "€ 3,90",
   "type": "main",
   "allergens": []
  },
  {
   "kind": "fish",
   "name": "Alaska pollak italiano",
   "price": "€ 3,60",
   "type": "main",
   "allergens": []
  },
  {
   "kind": "vegetarian",
   "name": "Moussaka met seitan",
   "price": "€ 4,70",
   "type": "main",
   "allergens": []
  }
 ],
 "open": true,
 "vegetables": [
  "Bloemkool",
  "Prinsessengroenten"
 ],
 "message": "Alle studenten krijgen op vertoon van Hydra 150% korting."
}
```

A menu object consists of:

| Field        | Description                                                                                                                                                                                        |
|--------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `date`       | The date of the menu. The date's format follows ISO 8601:2004's extended format (`YYYY-MM-DD`).                                                                                                    |
| `open`       | If set to `true`, the resto is open, otherwise not. If set to `false`. <br><br>Note that this is no guarantee: some days (like the weekends) are simply not present in the output.                 |
| `vegetables` | A list of available vegetables.                                                                                                                                                                    |
| `meals`      | A list of meal objects (see below).                                                                                                                                                                |
| `message`    | Optional field containing a message to be displayed. Used for exceptional closures or changes in the menu. For example, if `open` is `false`, the message could be an explanation for the closure. |

A meal object consists of:

| Field       | Description                                                                                                                                                              |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `kind`      | The kind of the meal. Expected values are currently `meat`, `fish`, `soup`, `vegetarian` or `vegan`. Applications must be able to handle changes to the possible values. |
| `name`      | The name of the meal.                                                                                                                                                    |
| `price`     | Textual representation of the price.                                                                                                                                     |
| `type`      | The meal type. Is currently `main` or `side`, but applications must be able to handle changes to the possible values.                                                    |
| `allergens` | List of allergens, matched on a best-efforts basis from the [allergen information](#allergen-information).                                                               |

> **Warning**
> The allergen information, like all other information in the API, is available on a best-efforts basis.
> Particularly, this information IS NOT FIT to replace the legally mandated information about allergens.
> When showing these data to users, please inform them of this and link to the web page.

How an application handles changes to possible values (indicated above where this is applicable), is not specified.
The application might simply ignore new values.

### Regular sandwiches

**Endpoint**: `GET /sandwiches/static.json`

Lists available regular sandwiches, their price and their ingredients. Sample output:

```json
[
 {
  "ingredients": [
   "brie",
   "honing",
   "pijnboompitten",
   "sla"
  ],
  "name": "Brie",
  "price_medium": "2.40",
  "price_small": "1.50"
 }
]
```

| Field          | Description                                         |
|----------------|-----------------------------------------------------|
| `ingredients`  | A list of the ingredients in the sandwich.          |
| `name`         | The name of the sandwich.                           |
| `price_medium` | The (textual) price in euros for a normal sandwich. |
| `price_small`  | The (textual) price in euros for a small sandwich.  |

### Weekly sandwiches overview

**Endpoint**: `GET /sandwiches/overview.json`

Lists all upcoming ecological sandwiches of the week ("ecologisch broodje van de week"). Output is in the same format
as [Weekly sandwiches yearly](#weekly-sandwiches-yearly).

### Weekly sandwiches yearly

**Endpoint**: `GET /sandwiches/{year}.json`

**Parameters**:

- _year_ -- Which year you want the sandwiches of. Values must be a positive integer. Currently, the earliest available
  year is 2019 (but this might change in the future). ISO format: `YYYY`.

Starting in academic year 2020-2021, this is listed as "groentespread".

Lists all sandwiches which were or are available in the specified year. Sample output:

```json
[
 {
  "start": "2019-09-16",
  "end": "2019-09-20",
  "ingredients": [
   "gebakken champignons met tofu (soja)",
   "mayonaise",
   "basilicum"
  ],
  "name": "Champignonsalade",
  "vegan": false
 }
]
```

| Field         | Description                                                                                                                      |
|---------------|----------------------------------------------------------------------------------------------------------------------------------|
| `ingredients` | A list of the ingredients in the sandwich.                                                                                       |
| `name`        | The name of the sandwich.                                                                                                        |
| `start`       | Inclusive start date on which the sandwich is available. The date's format follows ISO 8601:2004's extended format (YYYY-MM-DD). |
| `end`         | Inclusive end date on which the sandwich is available. The date's format follows ISO 8601:2004's extended format (YYYY-MM-DD).   |
| `vegan`       | Boolean indicating if the sandwich is vegan or not (not to be confused with vegetarian).                                         |

### Salad bowls

**Endpoint**: `GET /salads.json`

Lists available salad bowls, their price and a description. Sample output:

```json
[
 {
  "description": "Assortiment groenten, mozzarella, tomaat, basilicum pesto en sla",
  "name": "Tomaat-mozzarella",
  "price": "3.00"
 }
]
```

| Field         | Description                                                                    |
|---------------|--------------------------------------------------------------------------------|
| `description` | A description of the salad bowl. Often contains information about ingredients. |
| `name`        | The name of the salad bowl.                                                    |
| `price`       | The price in euros for a normal sandwich (this is a string).                   |

### Allergen information

**Endpoint**: `GET /allergens.json`

A list of allergen information per food category.
While the names of the meals and categories are in lower case,
they are otherwise not modified from the webpage from which they are scraped.
Since that webpage is made manually, it is very possible that the names used here do not match the ones used on the
menu.

> **Warning**
> This parser, as all other information in the API, is available on a best-efforts basis.
> Particularly, this information IS NOT FIT to replace the legally mandated information about allergens.
> When showing these data to users, please inform them of this and link to the web page.

Sample output:

```json
{
 "warme maaltijden: vis": {
  "fishstick van kabeljauw": [
   "gluten",
   "vis",
   "vis - msc"
  ]
 },
 "warme maaltijden: vlees": {
  "balletjes in tomatensaus": [
   "ei",
   "gluten",
   "melk",
   "selderij",
   "varken"
  ]
 }
}
```
