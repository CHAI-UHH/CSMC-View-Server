/* Generic viewer for use with CSMC files
 2024 - 2025 Magnus Bender
   Institute of Humanities-Centered Artificial Intelligence (CHAI)
   Universitaet Hamburg
   https://www.chai.uni-hamburg.de/~bender
   Aarhus University
   https://person.au.dk/magnus@mgmt.au.dk
 released under the terms of GNU Public License Version 3
   https://www.gnu.org/licenses/gpl-3.0.txt
*/

/**
 * @file Viewer Config file, part of 'raw', defines global constants.<br>
 * 
 * When configuring the viewer please make sure to follow the notes and comments here.
 * It is necessary that no java script errors are here, otherwise the viewer will not start at all.
 * If there are configuration errors, the viewer will show error messages on startup (or at least try to).<br>
 * 	- Set 'VIEWER_CONFIG.debug = true' while fiddling with this file and<br>
 * 	- disable the browser cache or use a private window etc.<br>
 * 
 * <br><br>
 * Also see the example config in ./dist/ !!
 * @namespace config
 */

/**
 * Version of this config file (do not change!).
 * 	Currently no use, later this will allow a viewer to be able to identify older and newer versions of a config file.
 * 	When there are different ways to configure (newer) viewers, the viewer can select the correct processors.
 * @global 
 * @constant {integer}
 */
const CONFIG_VERSION = 1;

/**
 * General configuration of viewer.<br>
 * 	See the comments for each key in the dictionary
 * @global 
 * @constant {dictionary}
 */
const HIDE_CITATION = true;

const VIEWER_CONFIG = {
	// css (jQuery) selector of html element, the viewer populates in
	"element" : "div#viewer", 
	// de-/active languages 
	"languages" : [
		"en",
		"de"
	],
	// run the viewer in debug mode (uses less caching, etc.)
	"debug" : true,
	// the base url/ path (with trailing slash)
	"base" : "./",
	// location of assets file (relative to 'base')
	"assets" : "static/assets.json",
	// some information about the data shown by the viewer (will also be included in export)
	"about" : {
		// heading (applied to h1 of 'show=true') of the page 
		"heading" : "EXAMPLE Viewer",
		// title of the page (applied if 'show=true')
		"title" : "Demo EXAMPLE Viewer", 
		// authors of the data 
		"authors" : "EXAMPLE Authors",
		// affiliation of the authors
		"affiliation" : "University of EXAMPLEs",
		// a link with more information about the data/ project/ ...
		"url" : "https://www.example.org/EXAMPLE.html",
		
		// show the meta information in the viewer/ on the page
		"show" : true
	}
};

/**
 * A uuid to identify this data set (used for caching)
 * 	Generate a random one, e.g., by 'python3 -c 'import uuid; print(uuid.uuid4())''
 * @global 
 * @constant {string}
 */
const DATA_UUID = '{{ uuid }}'; 
/**
 * the main data set (this is displayed in the primary table):<br>
 *	use a key in 'DATA_FILES'
 * @global 
 * @constant {string}
 */
const MAIN_DATA = "maininput";  
/**
 * specify all the data sets to load:<br>
 *	the key is the name of the database table used internally<br>
 *	See the comments for each key in the dictionary
 * @global 
 * @constant {dictionary}
 */
const DATA_FILES = {
	"maininput" : {
		"urls" : [  
			// the location(s) of the files to load:
			//	multiple files need to share the same column names and are only supported for csv data;
			//	relative to 'VIEWER_CONFIG.base';
			//	use the same file/ urls with all tables when using sqlite (one db file with multiple tables called like keys of 'DATA_FILES')
			"raw/input_html.csv"
		],
		// type of data: 'csv' or 'sqlite' for sqlite dbs:
		//	when loading a sqlite db, it is still necessary to make sure that all column types are specified correctly below  
		//	use the export function of either SQL schema or SQL database after loading CSV
		"type" : "csv",
		// all the columns used in the csv or database (or the ones to show/ load):
		//	the oder here determines the order for display, the order in the csv/ db may be different;
		//	if using sqlite type, make sure the columns specified here match the schema of the db (including keys!)
		"columns" : {
			// for each column name specify a string defining this column:
			// the format ist "name:value" or only "name", "<>" is used around placeholders, "|" is used for alternatives:
			//	"type:<int|text|html|geo|image|link>" or custom type, then add to RENDER_TYPES_HTML and RENDER_TYPES_PLAIN:
			//		"geo" contains geographic coordinates as two decimal values of Latitude and Longitude separated by ', ',
			//			e.g., '53.561049341278895, 9.995146272855523'. Will be displayed like text, but if 'USE_MAP=true'
			//			in detail view a map is shown and with "selector" a map is used as selector;
			//		"link" will become clickable hyperlink;
			//		"image" is a link to an image file to display (make sure to use relative path in csmc file or full [permanent] url),
			//			image sliders are based on bootstrap carousel, access via bootstrap.Carousel.getOrCreateInstance('<div#id>');
			//	"primary" becomes primary key;
			//	"foreign:<data>" becomes a foreign key, "<data>" must be name of foreign table (key in 'DATA_FILES'):
			//		Will insert *joined data*/ columns from the foreign table at this point;
			//		This may be a single value of the primary key in foreign table or with type:int also a list (separate by ',') of references to foreign table
			//	"name:<name>" to change the display name ('<name>' must not contain ',');
			//	"csv:<name>" set the name of the column in csv file, if different to name used by viewer;
			//	"bg:<hex|css name>" set the background color in detail popup; 
			//	"group:<name>" group this values in detail-popup, will also be set as css class
			//	"selector" show a selector for categories of this value on top:
			//		alteratively: "selector:<parent>" with name of parent column (in this table), this defines a hierarchy beneath selectors,
			// 			values of this selector are only enabled only if value of parent fits ('<parent>' must not contain ',');
			//	"hide" hide column per default, but can be shown with a button;
			//	"detail" column will be hidden and only shown in detail popup;
			//	"internal" column will be hidden and never shown;
			//	"sort" sort rows by this column (if not set primary used; this is also sort order for foreign tables)
			//	"title" use this value as title for detail popups (else uses primary key)
			// 	"truncate" truncate the display in table cells to three rows
			//	"lunr" allow full text search only on this column
			//	"row" show the values as two rows in detail view, instead of two columns
			"ID" : "type:int,primary",
			"Name" : "type:text",
		}
	}
};

/**
 * the db engine to use:<br>
 *	"dexie" (lightweight, uses caching and indexed db) does not allow sqlite type in 'DATA_FILES';<br>
 *	"sqlite" (heavier, more powerful);
 * @global 
 * @constant {string}
 */	
const DB_ENGINE = "dexie"; 
/**
 * use powerful full text search<br>
 *	will require significantly more memory
 * @global 
 * @constant {boolean}
 */
const USE_LUNR = true; 

/**
 * activate map support<br>
 *	allows columns of type 'geo' with geographic coordinates, the places will be shown on a map<br>
 * @global 
 * @constant {boolean}
 */
const USE_MAP = true; 

/**
 * Citation keys may be json objects, text, or int, but int are strongly preferred<br>
 *	get the citation key of a primary key value
 * @global 
 * @constant {function}
 * @example (p) => parseInt(p)
 */
const PRIMARY_KEY2CITATION_KEY = (p) => parseInt(p);
/**
 * Citation keys may be json objects, text, or int, but int are strongly preferred<br>
 * 	get the primary key of a citation key value
 * @global 
 * @constant {function}
 * @example (c) => parseInt(c)
 */
const CITATION_KEY2PRIMARY_KEY = (c) => parseInt(c);

/**
 * Rendering of data items<br>
 * 	per default there is a rendering for columns of type 'text', 'html', and 'int'<br>
 * 	other types can be specified in 'DATA_FILES.<>.columns' when providing a rendering function here<br>
 * 	is is also possible to overwrite a default function for the types 'text', 'html', and 'int' here<br>
 * <br><br>
 * render to html code (used for view etc.);<br>
 * The function gets two parameters: '(value, row) => ...', where row the is the full row object
 * @global 
 * @constant {dictionary<function>}
 */
const RENDER_TYPES_HTML = {};

/**
 * Rendering of data items<br>
 * 	per default there is a rendering for columns of type 'text', 'html', 'geo', and 'int'<br>
 * 	other types can be specified in 'DATA_FILES.<>.columns' when providing a rendering function here<br>
 * 	is is also possible to overwrite a default function for the types 'text', 'html', 'geo', and 'int' here<br>
 * <br><br>
 * render to plain text (used for search etc.);<br>
 * The function gets one parameter: '(value) => ...'
 * @global 
 * @constant {dictionary<function>}
 */
const RENDER_TYPES_PLAIN = {};

/**
 * Rendering of data items<br>
 * 	per default there is a rendering for columns of type 'text', 'html', 'geo', and 'int'<br>
 * 	other types can be specified in 'DATA_FILES.<>.columns' when providing a rendering function here<br>
 * 	is is also possible to overwrite a default function for the types 'text', 'html', 'geo', and 'int' here<br>
 * <br><br>
 * render to html for the detail view in popup, if not set, falls back to html<br>
 * The function gets two parameters: '(value, row) => ...', where row the is the full row object
 * @global 
 * @constant {dictionary<function>}
 */
const RENDER_TYPES_DETAIL = {};