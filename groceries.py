#!/usr/bin/python3

from config import Config
from trello.checklist import Checklist
import datetime


def main():
    card_name = datetime.datetime.strftime(datetime.datetime.now(), '%Y/%m/%d %H:%M')
    c = Config()
    client = c.connection

    grocery_board = client.get_board(c.board_id)
    trip_list = get_list('Trips', grocery_board)
    usual_list = get_list('Usual', grocery_board)
    next_trip_list = get_list('Next trip', grocery_board)
    recipes = get_list('Recipes', grocery_board)

    usual_items = get_usual_items(usual_list)
    last_trip = get_last_trip(trip_list)
    if last_trip is not None:
        add_missed_items(next_trip_list, last_trip, usual_items)

    lists_to_use = [usual_list, next_trip_list, recipes]
    # Get the list of groceries from the Usual Trello list
    items = get_item_list(lists_to_use)
    card = create_trip(card_name, trip_list, items, position='top')


def get_last_trip(trip_list):
    today = datetime.datetime.now()
    latest = 0
    c = None
    for card in trip_list.list_cards():
        try:
            card_date = datetime.datetime.strptime(card.name, '%Y/%m/%d')
        except ValueError as e:
            card_date = datetime.datetime.strptime(card.name, '%Y/%m/%d %H:%M')

        delta = days_between(today, card_date)
        if latest == 0:
            latest = delta
            c = card
        elif delta < latest:
            latest = delta
            c = card
    return c


def add_missed_items(dst_list, last_trip_card, usual_items):
    checklist = last_trip_card.checklists[0]
    for item in checklist.items:
        if item['checked'] == False:
            if item.name not in usual_items:
            # Need to figure out a way to un-archive a card
                dst_list.add_card(name + ' - Missed from last trip')
            

# https://stackoverflow.com/a/8419655
def days_between(d1, d2):
    return abs((d2 - d1).days)
        

def get_lists(names, board):
    lists = []
    for t_list in board.list_lists():
        if t_list.name in names:
            lists.append(t_list)
    return lists


def get_list(name, board):
    for t_list in board.list_lists():
        if t_list.name == name:
            return t_list
    return None


def get_usual_items(usual_list):
    l = []
    for card in usual_list.list_cards():
        l.append(card.name)
    return l


def add_recipe_items(recipe_list, recipe_name, items_list):
    print(items_list)
    for card in recipe_list.list_cards():
        if card.name.lower() == recipe_name.lower():
            # Checklist item will have the item name and label in it
            # e.g. 1 mango - Produce

            # Need a try except here at some point
            checklist = card.checklists[0]
            for item in checklist.items:
                item_name, item_label = item['name'].split('-')
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


def get_item_list(lists_to_use):
    list_order = ['Produce', 'Meat', 'Canned', 'Aisle 6', 'Soda',
                  'Dairy', 'Beauty', 'Frozen', 'Misc']
    items = {}
    recipe_list = None
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
                        
                    except KeyError as e:
                        items['Misc'].append(name)

                # Grocery items that are not needed that often and are one offs 
                if trello_list.name == 'Next trip':
                    card.set_closed(True)
    # Returns a list with items in their sections on how the Giant store is 
    #   oriented
    aisle_lists = []
    for aisle_list in list_order:
        aisle_lists += items[aisle_list]
    return aisle_lists


def create_trip(name, trello_list, items, desc=None, labels=None, due='null',
                source=None, position=None, assign=None,
                keep_from_source='checklist'):
    card = trello_list.add_card(name, desc=desc, labels=labels, due=due,
                         source=source, position=position, assign=assign,
                         keep_from_source=keep_from_source)
    card.add_checklist('Grocery list', items)
    return card


if __name__ == '__main__':
    main()
