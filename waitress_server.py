#!/var/www/trip/venv/bin/python3
from waitress import serve
import trip 


app = trip.create_app()
serve(app, host='0.0.0.0', port=6247)
