let imageUrls = [];

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.images) {
        imageUrls = message.images;
        console.log("Images collected:", imageUrls);
    }
    sendResponse({ success: true });
});

// Optional: add functionality to retrieve these images, for instance, in a popup or as needed.
chrome.action.onClicked.addListener((tab) => {
    chrome.scripting.executeScript({
        target: { tabId: tab.id },
        files: ["content.js"]
    });
});

