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


    usual_items = get_usual_items(usual_list)
    last_trip = get_last_trip(trip_list)
    if last_trip is not None:
        add_missed_items(next_trip_list, last_trip, usual_items)

    lists_to_use = [usual_list, next_trip_list]
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
    checklist = last_trip_card.checklist
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


def get_item_list(lists_to_use):
    list_order = ['Produce', 'Meat', 'Frozen', 'Canned', 'Aisle 6', 'Soda',
                  'Dairy', 'Beauty', 'Misc']
    items = {}
    for item in list_order:
        items[item] = []
    for trello_list in lists_to_use:
        for card in trello_list.list_cards():
            card_labels = card.labels
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
