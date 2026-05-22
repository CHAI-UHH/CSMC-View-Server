# Specification of the CSMC File Format
> Version 1.0.0 – 11-09-2024

.. toc::

The goal of the CSMC file format is to provide a simple way to store and share research data.
A CSMC file bundles raw research data along a dedicated viewer to visualize the data.

## Definitions
* CSMC File: A CSMC file according to this specification.
* Viewer: A software that can visualize research data.
* CSMC Software: A software that can view CSMC files.

## File Extension

The file extension to use for CSMC files is `.csmc`.

## File Structure

A CSMC file is a ZIP archive, but with the extension `.csmc` instead of `.zip`.
Thus, the MIME type is `application/zip`.

## Content of a CSMC File

The CSMC file has to contain an `index.html` at its top level.
This file is the entry point for the viewer.
Alongside the index file, the top level may only contain the following directories: `raw` and `static`.
Both directories are optional and may have subdirectories. All other files and directories are forbidden.

### `index.html`

The index file is the entry point for the viewer.
It has to be a valid HTML file.
The file is mandatory.
The index file is allowed to reference files in the `raw` and `static` directories using relative paths.
The viewer is forbidden to reference files outside the CSMC file.
Some CSMC software implementations may allow to reference files outside the CSMC file, but this is not part of the specification.

The index file has to contain the following placeholders:
* `<!-- CSMC-Branding -->` in the `<body>` tag. This placeholder can be replaced with the branding of the CSMC software.
* `<!-- CSMC-Legal -->` in the `<body>` tag.
	This placeholder can be replaced with the legal information of the CSMC software.
	This may be a footer and/or a floating, sticky element.
* `<!-- CSMC-Header -->` in the `<head>` tag. This placeholder can be replaced with references to custom assets by the CSMC software.

### `raw` directory

The `raw` directory contains the research data.
The directory is optional and is allowed to have subdirectories.
The `raw` directory is not allowed to contain utility files for the viewer.
The `raw` directory is allowed to contain any file format.
The CSMC software is not required to support all file formats.
The `raw` directory may contain raw research data or structured data suitable for the viewer.
It is allowed to contain both.
Duplicate data is allowed, but only if one version is raw and the other is structured.

### `static` directory

The `static` directory contains static files like images, CSS, or JavaScript files.
The directory is optional and is allowed to have subdirectories.
All filetypes are allowed.
The `static` directory is not allowed to contain research data.

## Viewing a CSMC File

To view a CSMC file, the user or the CSMC software has to extract the content of the CSMC file and open the `index.html` file in a web browser (allowing access to the directories `/raw` and `/static`).

## Implementation of CSMC Software

The CSMC software has to be able to show the user the viewer provided by the CSMC file.
The software is allowed to provide additional features like exporting the research data or creating CSMC files.

### Reference Implementation

A reference implementation of CSMC software is available as a live demo at [`https://csmc-view.chai.uni-hamburg.de/`](https://csmc-view.chai.uni-hamburg.de/).
The source code is currently not available.
The reference implementation is not part of the specification and may change at any time.
The reference implementation deviates from the specification in the following points:
* The reference implementation allows to reference OpenStreetMap tiles outside the CSMC file.

The reference implementation has the following features:
* Show the viewer of a CSMC file.
* Export the research data of a CSMC file.
* Create a CSMC file for certain research projects.
* Generate and view citations to data in CSMC files.

#### Additional Specifications for CSMC Files according to the Reference Implementation

The reference implementation has additional specifications for CSMC files.
These specifications are not part of the specification of the CSMC file format.

##### Citations

The reference implementation serves a citation javascript file.
This file is not part of the CSMC file, but is served by the reference implementation.
The viewer may use the functions provided by the citation javascript file to generate and show citations for the data in the CSMC file.

## (Sub-)Specification for Citations
The citation feature is mostly carried out by the `citation.js` injected via the `<!-- CSMC-Header -->`.
However, for using citations, the CSMC software and the viewer contained in a CSMC file both need to support citations.

### Overview
A citation can be obtained for a viewpoint of a viewer. 
The citation can then be used to *reopen* the viewer at the same viewpoint.
A viewer needs to display citation buttons (to get the citation link) at all citable viewpoint.
Additionally, a viewer needs to detect citation data provided by the CSMC Software.
Both can be easily done by using the `citation.js`.

The citations use the fragments available for default web urls, including DOIs.
Hence, the citation data is stored in the part after the `#` at the end of citation, i.e, a DOI.
For example, the citation `https://doi.org/10.25592/mdq0-7x79#22` refers to the DOI `10.25592/mdq0-7x79` and the citation data `22`.
In this case, `22` is the 22th poem.

### Technical Details
The `citation.js` provides a class `CSMC` and is well documented, see the source [here](https://github.com/CHAI-UHH/CSMC-View-Server/blob/main/server/web/public/js/citation.js).
This class only contains static methods and is used as namespace for all citation related functions available.
An exemplary viewer needs to implement two small things to support citations.

Besides `<!-- CSMC-Header -->` it is recommended to add `<script>class CSMC{static isAvailable(){return false;}}</script>` (exactly this string!) to the html header of the viewer's `index.html`.
This will be removed by the CSMC software when injecting the `citation.js`, but assure the viewer to work properly in CSMC software not supporting citations.

#### Open Citation Data
The viewer needs to check, if citation data is available, i.e, there is an `#...`.
And if there is data, the viewer needs to open the corresponding item.

```js
if(
	CSMC.isAvailable() && // check if citations available 
	CSMC.hasCitationData() // check if there is citation data `#...`
){ 
	var cite_data = CSMC.getCitationData(); // extract the citation data `#...`
	// change the viewport to show the item cited by `cite_data`
	cite_data
	// ...
}
```

#### Show Citation Links
For each citable item, the viewer needs to show a citation button or link containing the relevant citation data `#...`.

```js
if(CSMC.isAvailable()){ // check if citations available 
	var my_cite_data = 12; // get the citation data for this viewpoint
		// citation data may be numbers/integers, strings, or even JSON (list, dict) objects
		// 	but keep in mind, that small citation data is better than large one, 
		// 	because large data results in long urls `#....`!

	// generate the full citation link for 'my_cite_data'
	var citation_link = CSMC.getCitationLink(my_cite_data);

	if(citation_link !== false){ // 'citation_link' will be false on error 
		// show the link to the user, e.g., display
		`<a href="${citation_link}" target="_blank"><code>${citation_link}</code></a>` 

		// showing a *Copy Citation* Button is also easily possible
		// 	add a button to the page, e.g., display
		`<button id="copyCitation">Copy citation</button>` 
		//	add an event to copy the 'citation_link' when clicking the 
		//		'#copyCitation' button (all by using the CSMC class)
		CSMC.copyCitationButton('#copyCitation', citation_link);
	}
	else{
		// get an error message
		CSMC.getCitationLinkMessage();
	}
}
else { // citations not available, possibly show a message
	// e.g., display
	`Citations: Error (<em>Unsupported Viewer/ CSMC Software</em>)`
}
```
