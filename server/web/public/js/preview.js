function _showPopup(title, message) {
	// Create background overlay
	var overlay = document.createElement('div');
	overlay.style.position = 'fixed';
	overlay.style.top = '0';
	overlay.style.left = '0';
	overlay.style.width = '100%';
	overlay.style.height = '100%';
	overlay.style.backgroundColor = 'rgba(0,0,0,0.5)';
	overlay.style.zIndex = '9999';
	
	// Create popup container
	var popup = document.createElement('div');
	popup.style.position = 'fixed';
	popup.style.top = '0';
	popup.style.left = '50%';
	popup.style.transform = 'translateX(-50%)';
	popup.style.backgroundColor = '#ff0000';
	popup.style.color = '#ffffff';
	popup.style.padding = '20px';
	popup.style.borderRadius = '5px';
	popup.style.zIndex = '10000';
	popup.style.textAlign = 'center';
	popup.style.width = '80%';
	popup.style.maxWidth = '400px';
	popup.style.marginTop = '50px';
	
	// Create title
	var titleElement = document.createElement('h2');
	titleElement.innerText = title;
	titleElement.style.marginTop = '0';
	popup.appendChild(titleElement);
	
	// Create message
	var messageElement = document.createElement('p');
	messageElement.innerText = message;
	popup.appendChild(messageElement);
	
	// Create link button
	var linkButton = document.createElement('a');
	linkButton.href = 'https://www.fdr.example.com/deposit';
	linkButton.target = '_blank';
	linkButton.innerText = 'Open FDR Upload Form';
	linkButton.style.display = 'inline-block';
	linkButton.style.backgroundColor = '#ffffff';
	linkButton.style.color = '#ff0000';
	linkButton.style.padding = '10px 20px';
	linkButton.style.textDecoration = 'none';
	linkButton.style.borderRadius = '5px';
	linkButton.style.marginTop = '20px';
	popup.appendChild(linkButton);
	
	// Create close button
	var closeButton = document.createElement('button');
	closeButton.innerText = 'Close';
	closeButton.style.position = 'absolute';
	closeButton.style.top = '10px';
	closeButton.style.right = '10px';
	closeButton.style.backgroundColor = '#ffffff';
	closeButton.style.color = '#ff0000';
	closeButton.style.border = 'none';
	closeButton.style.padding = '5px 10px';
	closeButton.style.cursor = 'pointer';
	closeButton.onclick = function() {
	  document.body.removeChild(overlay);
	};
	popup.appendChild(closeButton);
	
	// Append elements to body
	overlay.appendChild(popup);
	document.body.appendChild(overlay);
}  

if(CSMC.isAvailable() && CSMC.isRemotePreview()) {
	document.addEventListener('DOMContentLoaded', function() {
		_showPopup("Preview Only", "This is only a temporal preview and will be deleted in a few days. Please upload your CSMC file to the FDR to create a permanent version.");
	});
}