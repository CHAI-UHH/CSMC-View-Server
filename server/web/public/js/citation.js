"use strict";

/*
# CSMC File Server -- FastAPI implementation
# 	(c) 2024 Magnus Bender
# 	Institute of Humanities-Centered Artificial Intelligence (CHAI), Universitaet Hamburg
# 		https://www.philosophie.uni-hamburg.de/chai/personen/bender.html
# 	All rights reserved!
*/

class CSMC {

	static _get_link_error_message = null;
	static _window_location_hostname = window.location.hostname;

	static _host_id2doi = {
		"https://staging-rdm.example.com|some-id" : "https://doi.org/10.xxx/some-id",
	};
		

	/**
	 * Check is the CSMC class is available.
	 * @returns bool
	 */
	static isAvailable() {
		return true;
	}

	/**
	 * Check if the Viewer is running on the remote CSCM-View server.
	 * @returns boolean
	 */
	static isRemoteView() {
		return this._window_location_hostname === 'csmc-view.chai.uni-hamburg.de' && window.location.pathname.startsWith("/view/");
	}

	/**
	 * Check if the Viewer is running as preview on the remote CSCM-View server.
	 * @returns boolean
	 */
	static isRemotePreview() {
		
		if(this._window_location_hostname === "localhost" || this._window_location_hostname === "127.0.0.1"){
			return window.location.pathname.startsWith("/preview/");
		}

		return this._window_location_hostname === 'csmc-view.chai.uni-hamburg.de' && !window.location.pathname.startsWith("/view/");
	}

	/**
	 * Check if the Viewer is running in the local previewer. 
	 * @returns boolen
	 */
	static isLocalPreview() {
		return this._window_location_hostname !== 'csmc-view.chai.uni-hamburg.de';
	}

	/**
	 * Check if it is possible to view and generate citations in this Viewer.
	 * @returns boolean
	 */
	static isCitationAvailable(){
		return this.isRemoteView();
	}

	/**
	 * Check if there is citation data available to the Viewer (if there is data, it should be used)
	 * @returns  boolean
	 */
	static hasCitationData(){
		return this.isCitationAvailable() && window.location.hash.length > 0 && /^\#[A-Za-z0-9\+\/\=]+$/.test(window.location.hash)
	}

	/**
	 * Get the citation data available to the Viewer.
	 * @returns string|int|JSON-object
	 */
	static getCitationData(){
		return this.hasCitationData() ? this._decode(window.location.hash) : null;
	}

	static _decode(data){
		if( /^\#[\d]+$/.test(data) ){ // data is an integer
			return parseInt(data.substring(1));
		}
		else { // data is base64 encoded
			var str = atob(data.substring(1));
			// check if JSON or just string
			return (str.charAt(0) == "[" || str.charAt(0) == "{") ? JSON.parse(str) : str.trim();
		}
	}

	/**
	 * Generate the citation link for the item to cite specified via `data`. The Viewer will later get the data
	 * back via `getCitationData()` and shall open the item.
	 * Thus, the viewer needs to identify some type of ID for an item, use this ID as data and open the item if the ID
	 * is provided.
	 * `data` should be as short as possible, it may be an integer, string, list or dictionary (the two last are encoded using JSON)
	 * @param {string|int|JSON(list or dictionary)} data 
	 * @returns string|false
	 */
	static getCitationLink(data) {
		if(!this.isCitationAvailable()){
			this._get_link_error_message = "Citations can only be created for published Viewers."
			return false;
		}

		var url_parts = window.location.pathname.match(
			/^\/view\/(.*)\/record(s?)\/([A-Za-z\_\-0-9]+)\/files\/([A-Za-z\_\-0-9%\ \.]+)\.csmc\/(?:index\.html)?$/
		);
		if(url_parts === null){
			this._get_link_error_message = "The url of this Viewer does not fulfil the requirements."
			return false;
		}

		if(url_parts[1] === "https://www.fdr.uni-hamburg.de"){
			var doi = `https://doi.org/10.xx/yy.${url_parts[3]}`;
		}
		else if(this._host_id2doi.hasOwnProperty(`${url_parts[1]}|${url_parts[3]}`)){
			var doi = this._host_id2doi[`${url_parts[1]}|${url_parts[3]}`];
		}
		else{
			var doi = `${url_parts[1]}/record${url_parts[2]}/${url_parts[3]}`;
		}

		var encoded = this._encode(data);
		if( encoded === false ){
			return false;
		}
		return doi + encoded;
	}

	static _encode(data){
		if(typeof(data) === 'number'){
			return `#${data}`; // just append simple number 
		}
		else if(typeof(data) === 'string'){
			if(data.charAt(0) == "[" || data.charAt(0) == "{"){ // does string look like JSON?
				data = " " + data; // just add an space as prefix (will be trimmed by `_decode`)
			}
			while(/^\d+$/.test(btoa(data))){ // make sure the base64 does not contain only numbers
				data += " "; // add one space at the end
			}
			return "#"+btoa(data);
		}
		
		try{
			var data = JSON.stringify(data);
			if(data.charAt(0) == "[" || data.charAt(0) == "{"){ // make sure that only list or dictionary
				while(/^\d+$/.test(btoa(data))){ // make sure the base64 does not contain only numbers
					data += " "; // add one space at the end
				}
				return "#"+btoa(data);
			}
			else{
				this._get_link_error_message = "The JSON data for the citation does not contain a list or dictionary."
			}
		} catch {
			this._get_link_error_message = "The data for the citation can not be encoded via JSON."
		}

		//this._get_link_error_message = "The data for the citation does not fulfil the requirements."
		return false;
	}

	/**
	 * Get an error message if `getCitationLink()` fails.
	 * @returns string
	 */
	static getCitationLinkMessage(){
		var msg;
		if(this._get_link_error_message === null){
			if(this.getCitationLink() === false){
				msg = this._get_link_error_message 
			}
			else{
				return false;
			}
		}
		else{
			msg = this._get_link_error_message 
		}
		this._get_link_error_message = null;
		return msg;
	}

	/**
	 * This function allows to add a button for copying the citation of a viewer to clipboard.
	 * It assumes there is a button displayed on the page (e.g., '<button id=copyCite>Copy Citation</button>')
	 * which should write the citation link into the user's clipboard. This button is referenced by 
	 * `element_or_selector`, either by a selector or dom element.
	 * When the button is clicked, the link will be written to the user's clipboard, the data is defined by 
	 * `link_or_data`. If it is a string starting with 'http' a link is assumed. Otherwise, `getCitationLink()` is
	 * used to get the link for the data.
	 * If `isCitationAvailable()` is false or `getCitationLink()` returns false, the button will become hidden.
	 * 
	 * @param {string|dom object} element_or_selector A DOM element or a selector representing a button which copies the data to clipboard
	 * @param {string|int|JSON(list or dictionary)} link_or_data The link or data to copy. 
	 * @param {boolean} assure_availability (optional, default=false) Also hide button if `isCitationAvailable()` is false but usable citation link given
	 */
	static copyCitationButton(element_or_selector, link_or_data, assure_availability=false){
		// assure that element_or_selector is an DOM element
		if(typeof(element_or_selector) === 'string'){
			element_or_selector = document.querySelector(element_or_selector);
		}

		// check if citation is available 
		if(assure_availability && !this.isCitationAvailable()){
			element_or_selector.style.display = "none";
		}

		// get the link from data, unless it is already data
		if(typeof(link_or_data) !== 'string' || !link_or_data.startsWith('http')){
			link_or_data = this.getCitationLink(link_or_data)
		}

		// data is invalid -> no link
		if(link_or_data === false){
			element_or_selector.style.display = "none";
		}

		//now data is to copy seems to be valid

		// ability to reset button
		var text_before = element_or_selector.textContent;
		var reset_button = () => {
			setTimeout(()=>{
				element_or_selector.textContent = text_before;
			}, 2000);
		}
		
		// listen for click and write clipboard
		element_or_selector.addEventListener('click', (e)=>{
			e.preventDefault();
			e.stopImmediatePropagation();
		
			navigator.clipboard.writeText(link_or_data).then(()=>{
				element_or_selector.textContent = '*Copied to clipboard*';
				reset_button();
			}).catch((e)=>{
				element_or_selector.textContent = '*Error copying to clipboard*';
				reset_button();
				console.error(e);
			});
		}, true);
	}
}