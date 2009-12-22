JS_builder
==========

`JS_builder` is a JavaScript dependency management tool. We can define for all files dependencies which are required e.g. file core.js must be add before all other files because it contains main namespace. Files are concatenated in the right order and minimize. When template are rendered and some packages must be added to that page system checks if there were some modifications in files from package and rebuild it automatically.

Installation
============
#. Add the `js_builder` directory to your Python path.

#. Add the `js_builder` to your INSTALLED_APP setting.

#. Add a setting `JS_BUILDER_SOURCE`. This should be an absolute path to the directory with source JavaScript files. For example::
    
	JS_BUILDER_SOURCE = os.path.join(os.path.dirname(__file__, "media", "js", "internal")


Configuration
=============

Error logging
-------------

