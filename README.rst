JS_builder
==========

Installation
============
#. Add the `js_builder` directory to your Python path.`

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

#. In the template add::

    	{% load js_tags %}
    	{% js_package 'core' %}

   When template will be rendered this will we replaced by::

   	<script type='text/javascript' src='{{ MEDIA_URL }}p1.js'>

   Also system will check if some files from package `p1` were modified since last building and if there were some changes `JS_builder` will rebuild that package.

Configuration
=============

Error logging
-------------

