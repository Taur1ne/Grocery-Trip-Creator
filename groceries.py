#!/usr/bin/python3

from config import Config
from trello.checklist import Checklist


def main():
    c = Config()
    client = c.connection

    grocery_board = client.get_board(c.board_id)
    trip_list = get_list('Trips', grocery_board)
    usual_list = get_list('Usual', grocery_board)

    # Get the list of groceries from the Usual Trello list
    items = get_item_list(usual_list)
    card = create_trip('2019/06/24', trip_list, items)


def get_list(name, board):
    for t_list in board.list_lists():
        if t_list.name == name:
            return t_list
    return None


def get_item_list(trello_list):
    items = []
    produce = []
    meat = []
    canned = []
    soda = []
    dairy = []
    frozen = []
    misc = []

    for card in trello_list.list_cards():
        card_labels = card.labels
        labels = [label.name for label in card_labels]
        name = card.name
        if 'Produce' in labels:
            produce.append(name)
        elif 'Meat' in labels:
            meat.append(name)
        elif 'Frozen' in labels:
            frozen.append(name)
        elif 'Canned' in labels:
            canned.append(name)
        elif 'Soda' in labels:
            soda.append(name)
        elif 'Dairy' in labels:
            dairy.append(name)
        else:
            misc.append(name)

    # Returns a list with items in their sections on how the Giant store is 
    #   oriented
    return produce + meat + canned + soda + dairy + frozen 


def create_trip(name, trello_list, items, desc=None, labels=None, due="null",
                source=None, position=None, assign=None,
                keep_from_source="checklist"):
    card = trello_list.add_card(name, desc=desc, labels=labels, due=due,
                         source=source, position=position, assign=assign,
                         keep_from_source=keep_from_source)
    card.add_checklist('Grocery list', items)
    return card


if __name__ == '__main__':
    main()
