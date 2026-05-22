// Function to log the current title, URL, and timestamp to localStorage
function _history_logToLocalStorage() {
	
	if(localStorage) {

		const currentTitle = document.title;
		const currentURL = window.location.href;
		const currentTimestamp = new Date().toISOString();
	
		const logEntry = {
			title: currentTitle,
			url: currentURL,
			timestamp: currentTimestamp
		};
	
		let logs = JSON.parse(localStorage.getItem('history')) || [];
		logs.push(logEntry);
		
		// Limit the history to 20 entries
		if(logs.length > 20) {
			logs = logs.slice(logs.length - 20);
		}

		localStorage.setItem('history', JSON.stringify(logs));

	}

}

document.addEventListener('DOMContentLoaded', _history_logToLocalStorage);