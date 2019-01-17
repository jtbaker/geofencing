# GeoFencing
A REST Web application built using the [Python-Responder](https://python-responder.org/en/latest/) web framework for the back end, and Vue as well as Leaflet on the front end.

Python 3.6+

Designed to streamline the process of integrating new geography data into the freightwaves geofencing database.

Configure the system environment variables `fwdbhost`, `fwdbuser`, `fwdbpass`, and `fwdbhost`.

To run, clone or download this repository, navigate into the folder, and run:

`pip install -r requirements.txt`

To run the server on something other than `localhost` add a keywod argument `router.run()` like `address=0.0.0.0` in the main block of `init.py`.

Then:

`python init.py`
