from trello import TrelloClient


class Config():
    connection = TrelloClient(
            # Found here: https://trello.com/app-key
            api_key='',
            api_secret='',
            token='')
    # Found in the URL after the /b/
    # $HERE is the board_id
    # https://trello.com/b/$HERE/$BOARD_NAME
    
    board_id = ''
