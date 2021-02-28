#!/usr/bin/python3
import argparse
import datetime

from typing import Dict, List, Optional

from config import Config
import trello


def main():
    """Create a grocery check list from Trello cards"""

    args = get_args()
    print(f'short trip: {args.short_trip}')
    print(f'last trip: {args.last_trip}')

    card_name: str = datetime.datetime.strftime(datetime.datetime.now(),
                                                '%Y/%m/%d %H:%M')
    c = Config()
    client = c.connection

    grocery_board: trello.Board = client.get_board(c.board_id)
    trip_list: trello.List = get_list('Trips', grocery_board)
    usual_list: trello.List = get_list('Usual', grocery_board)
    next_trip_list: trello.List = get_list('Next trip', grocery_board)
    recipes: trello.List = get_list('Recipes', grocery_board)

    usual_items = get_usual_items(usual_list)

    if args.last_trip:
        last_trip = get_last_trip(trip_list)
        if last_trip is not None:
            add_missed_items(next_trip_list, last_trip, usual_items)

    lists_to_use = [next_trip_list, recipes]
    if not args.short_trip:
        lists_to_use.append(usual_list)
    # Get the list of groceries from the Usual Trello list
    items = get_item_list(lists_to_use)

    print(f'Creating new trip: {card_name}')
    create_trip(card_name, trip_list, items, position='top')


def get_last_trip(trip_list: trello.List) -> Optional[trello.Card]:
    """returns the last trip card if it exists."""
    today = datetime.datetime.now()
    latest = 0
    c: trello.Card = None
    for card in trip_list.list_cards():
        try:
            card_date = datetime.datetime.strptime(card.name, '%Y/%m/%d')
        except ValueError:
            card_date = datetime.datetime.strptime(card.name, '%Y/%m/%d %H:%M')

        delta = days_between(today, card_date)
        if latest == 0:
            latest = delta
            c = card
        elif delta < latest:
            latest = delta
            c = card
    return c


def add_missed_items(dst_list: trello.List, last_trip_card: trello.Card,
                     usual_items: List[str]):
    """Add missed items from the last trip to the new trip's list."""
    checklist: trello.Checklist = last_trip_card.checklists[0]
    for item in checklist.items:
        if item['checked'] is False:
            name = item['name']
            if name not in usual_items:
                # Need to figure out a way to un-archive a card
                dst_list.add_card(name + ' - Missed from last trip')


# https://stackoverflow.com/a/8419655
def days_between(d1, d2):
    return abs((d2 - d1).days)


def get_lists(names: List[str], board: trello.Board) -> List[trello.List]:
    """returns the Trello lists from the Trello board"""
    lists: List[trello.List] = []
    for t_list in board.list_lists():
        if t_list.name in names:
            lists.append(t_list)
    return lists


def get_list(name: str, board: trello.Board) -> Optional[trello.List]:
    """returns a trello list if it exists on the Trello board"""
    for t_list in board.list_lists():
        if t_list.name == name:
            return t_list
    return None


def get_usual_items(usual_list: trello.List) -> List[str]:
    """returns list of item names"""
    l: List[str] = []
    for card in usual_list.list_cards():
        l.append(card.name)
    return l


def add_recipe_items(recipe_list: trello.List, recipe_name: str,
                     items_list: Dict[str, List[str]]):
    """Adds multiple items to a list from a card labelled as a recipe.

    Takes a trello card with the recipe label and searches for a matching card
    in the "Recipe" list. It will then add items from the checklist within the
    matched card. For example: If a "peanut butter and jelly sandwich" card is
    added to the "Next trip" list and labelled as "Recipe", then the function
    will search the "Recipes" list for a "peanut butter and jelly sandwich"
    card. That card will have a check list with multiple items and their labels
    such as: peanut butter - Bread, grape jelly - Canned, wheat bread - Bread.
    The aforementioned itmes will be added to the next trip's list.
    """
    print(items_list)
    for card in recipe_list.list_cards():
        if card.name.lower() == recipe_name.lower():
            # Checklist item will have the item name and label in it
            # e.g. 1 mango - Produce

            # Need a try except here at some point
            checklist = card.checklists[0]
            for item in checklist.items:
                item_name, item_label = item['name'].split(' - ')
                item_name = item_name.strip()
                item_label = item_label.strip()

                try:
                    if item_name not in items_list[item_label]:
                        items_list[item_label].append(item_name)
                    else:
                        new_name = '{} for {}'.format(item_name, recipe_name)
                        items_list[item_label].append(new_name)
                except KeyError as e:
                    print(e)
                    items_list[item_label].append(item_name)


def get_item_list(lists_to_use: List[trello.List]) -> List[str]:
    """returns a sorted list of grocery items based on section."""
    list_order = ['Produce', 'Meat', 'Canned', 'Aisle 6', 'Soda',
                  'Dairy', 'Beauty', 'Frozen', 'Misc']
    items: Dict[str, List[str]] = {}
    recipe_list: trello.List = None
    for trello_list in lists_to_use:
        if trello_list.name.lower() == 'recipes':
            recipe_list = trello_list
            break

    for item in list_order:
        items[item] = []
    for trello_list in lists_to_use:
        if trello_list.name.lower() != 'recipes':
            for card in trello_list.list_cards():
                card_labels = card.labels
                print(card_labels)
                if 'Recipe' in [label.name for label in card_labels]:
                    add_recipe_items(recipe_list, card.name, items)
                else:
                    if card_labels is not None:
                        labels = [label.name for label in card_labels]
                    else:
                        labels = ['Misc']

                    name = card.name
                    print(labels)
                    try:
                        items[labels[0]].append(name)

                    except KeyError:
                        items['Misc'].append(name)

                # Grocery items that are not needed that often and are one offs
                if trello_list.name == 'Next trip':
                    card.set_closed(True)
    # Returns a list with items in their sections on how the Giant store is
    #   oriented
    aisle_lists: List[str] = []
    for aisle_list in list_order:
        aisle_lists += items[aisle_list]
    return aisle_lists


def create_trip(name: str, trello_list: trello.List, items: List[str],
                desc: str = None, labels: List[trello.Label] = None,
                due='null', source=None, position=None, assign=None,
                keep_from_source='checklist') -> trello.Card:
    """Creates a grocery check list and places it in the "Next trip" list"""
    card = trello_list.add_card(name, desc=desc, labels=labels, due=due,
                                source=source, position=position,
                                assign=assign,
                                keep_from_source=keep_from_source)
    card.add_checklist('Grocery list', items)
    return card


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-lt', '--last-trip', action='store_true',
                        default=False, help='Add missing items from last trip')
    parser.add_argument('-st', '--short-trip', action='store_true',
                        default=False,
                        help='Only add items from the "Next trip" list')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    main()
