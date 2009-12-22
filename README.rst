JS_builder
==========

`JS_builder` is a JavaScript dependency management tool. We can define for all files dependencies which are required e.g. file core.js must be add before all other files because it contains main namespace. Files are concatenated in the right order and minimize. When template are rendered and some packages must be added to that page system checks if there were some modifications in files from package and rebuild it automatically.

Installation
============
#. Add the `js_builder` directory to your Python path.

#. Add the `js_builder` to your INSTALLED_APP setting.

#. Add a setting `JS_BUILDER_SOURCE`. This should be an absolute path to the directory with source JavaScript files. For example::
    
	JS_BUILDER_SOURCE = os.path.join(os.path.dirname(__file__, "media", "js", "internal")

#. Add a setting `JS_BUILDER_DEST` with absolute path to the directory with builded JavaScript packages e.g.::
   	
	JS_BUILDER_DEST = os.path.join(os.path.dirname(__file__), "media", "js", "public")

#. set `JS_BUILDER_PACKAGES` setting. It's a dictionary with definition of packages. For example::
   
	JS_BUILDER_PACKAGES = {
            "core": ["core.js", "ajax.js", "dom.js"],
            "ui": ["\*\*\*/ui/.\*\.js"]
    	}

#. In each JavaScript file we can define which other files are required e.g.::

	// require core.js
	// require ui.js

   Files `core.js` and `ui.js` will be added before that file so all dependencies will be met. After finding all depenendencies, files are concatenated in the right order and saved to the new JavaScript file. What are benefits of that? It reduces http request on site. This is important step to speed up your web site. Steve Souders describes this in “High Performance Web Sites” book. 

Configuration
=============

Error logging
-------------

