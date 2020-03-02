PythonistaWorkApp
=================

In Progress. Eventually will be handy toolset for pilots who also happen to have Pythonista
installed on their company iPads. 

Current Apps
------------

* ``__main__.py``: Shell Interface for calculating wind components, and max winds from a 
range of directions. 

Installation
------------

The app is currently best installed with ``git clone https://github.com/AirbusDriver/PythonistaWorkApp.git`` or just grab one of the zip/tar.gz
bundles in the [Release](https://github.com/AirbusDriver/PythonistaWorkApp/releases) section
of this repo. 

Road Map
--------

* unified gui for all plugins
* briefer.py: line select airports in company OPSPECS that you travel to frequently. Then grab quick METAR/TAF data

Winds Shell
---------

Currently, the wind calculation shell is the only thing implemented. The main entry point for the shell is in
the ``__main__.py`` file. This can be invoked by either running the ``__main__.py`` file directly or by running
``python3 -m work``... but, since you are presumably running this in pythonista, just run the file directly.
