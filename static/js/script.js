document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    
    // Variable to store session ID
    let sessionId = localStorage.getItem('chat_session_id') || '';
    
    // Function to automatically adjust the textarea size based on its content
    function autoResizeTextarea() {
        // Reset height to auto to get the correct scrollHeight
        userInput.style.height = 'auto';
        
        // Set height to match content (with maximum height applied via CSS)
        userInput.style.height = (userInput.scrollHeight) + 'px';
    }
    
    // Initialize textarea height
    autoResizeTextarea();
    
    // Add event listener to resize while user types
    userInput.addEventListener('input', autoResizeTextarea);
    
    // Function to add a message to the chat
    function addMessage(content, type) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', type);
        
        // Check if content is HTML (from markdown conversion)
        if (content.startsWith('<')) {
            messageDiv.innerHTML = content;
        } else {
            messageDiv.textContent = content;
        }
        
        chatMessages.appendChild(messageDiv);
        
        // Scroll to the end of the chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Function to send a message to the API
    async function sendMessage(message) {
        // Add user message to chat
        addMessage(message, 'user');
        
        // Add loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('message', 'bot', 'loading');
        loadingDiv.textContent = 'Thinking...';
        chatMessages.appendChild(loadingDiv);
        
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    message, 
                    session_id: sessionId 
                })
            });
            
            const data = await response.json();
            
            // Store received session ID
            if (data.session_id) {
                sessionId = data.session_id;
                localStorage.setItem('chat_session_id', sessionId);
            }
            
            // Remove loading indicator
            chatMessages.removeChild(loadingDiv);
            
            if (data.error) {
                addMessage(`Error: ${data.error}`, 'system');
            } else {
                addMessage(data.response, 'bot');
            }
        } catch (error) {
            // Remove loading indicator
            chatMessages.removeChild(loadingDiv);
            
            addMessage(`Error: ${error.message}`, 'system');
        }
    }
    
    // Function to handle message sending and reset textarea
    function handleSendMessage() {
        const message = userInput.value.trim();
        if (message) {
            sendMessage(message);
            userInput.value = '';
            // Reset textarea height after clearing
            userInput.style.height = 'auto';
            userInput.style.height = userInput.scrollHeight + 'px';
        }
    }
    
    // Event listener for send button
    sendButton.addEventListener('click', handleSendMessage);
    
    // Event listener for Enter key (but allow Shift+Enter for new lines)
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent default behavior to avoid adding a new line
            handleSendMessage();
        }
    });
    
    // Focus input field when page loads
    userInput.focus();
});

// Handle table of contents links
document.addEventListener('DOMContentLoaded', function() {
    const textContent = document.querySelector('.text-content');
    
    // Add click event listener to text content area for delegation
    textContent.addEventListener('click', function(e) {
        // Check if clicked element is a TOC link
        if (e.target.tagName === 'A' && e.target.getAttribute('href').startsWith('#section-')) {
            e.preventDefault();
            
            // Extract section ID from href
            const sectionId = e.target.getAttribute('href').substring(1);
            
            // Find corresponding section text based on ID
            let searchText;
            
            // Section map to simplify logic
            const sectionMap = {
                'section-1': "1. CODE OF CONDUCT POLICY",
                'section-2': "2. BOARD OF TRUSTEES CODE OF CONDUCT",
                'section-3': "3. CONFLICT OF INTEREST POLICY",
                'section-4': "4. CONFIDENTIALITY AGREEMENT",
                'section-5': "5. FINANCIAL POLICIES",
                'section-6': "6. OPERATIONAL POLICIES",
                'section-7': "7. COMPLIANCE POLICIES",
                'section-8': "8. TRAVEL POLICIES", 
                'section-9': "9. WHISTLEBLOWER PROTECTION",
                'section-5-1': "5.1 CREDIT CARD USAGE POLICY",
                'section-5-2': "5.2 DELEGATION OF AUTHORITY",
                'section-6-1': "6.1 DUTY ENTERTAINMENT GUIDELINES",
                'section-6-2': "6.2 GIFT POLICY",
                'section-7-1': "7.1 ANTI-CORRUPTION POLICY",
                'section-7-2': "7.2 NON-DISCRIMINATION POLICY",
                'section-8-1': "8.1 GENERAL TRAVEL POLICY",
                'section-8-2': "8.2 TRAVEL APPROVAL PROCESS"
            };
            
            // Alternatives for different text formats in the document
            const sectionAlternatives = {
                'section-5-1': ["5.1 CREDIT CARD USAGE", "5.1 CREDIT CARD USAGE POLICY (adopted"],
                'section-5-2': ["5.2 DELEGATION OF AUTHORITY", "5.2 DELEGATION OF AUTHORITY POLICY"]
            };
            
            // Get primary search text
            searchText = sectionMap[sectionId];
            
            if (searchText) {
                // Get complete document content
                const preElement = textContent.querySelector('pre');
                const text = preElement.textContent;
                
                // Search patterns in order of preference
                const searchPatterns = [
                    // Pattern 1: Separator line + section title
                    "=============================================================================\n" + searchText,
                    // Pattern 2: Just the section title
                    searchText,
                    // Pattern 3: For sections with special format (5.1, 5.2, etc.)
                    ...(sectionAlternatives[sectionId] || [])
                ];
                
                // Search for section using patterns in order
                let foundIndex = -1;
                for (const pattern of searchPatterns) {
                    const index = text.indexOf(pattern);
                    if (index !== -1) {
                        foundIndex = index;
                        break;
                    }
                }
                
                // If we found the section, scroll to it
                if (foundIndex !== -1) {
                    // Calculate approximate position
                    const lines = text.substring(0, foundIndex).split('\n');
                    const lineHeight = 22; // Approximate line height in pixels
                    const scrollPosition = lines.length * lineHeight;
                    
                    // Scroll to position with a small offset for context
                    textContent.scrollTop = scrollPosition - 50;
                    
                    // Briefly highlight the found section to make it easier to identify
                    highlightSection(preElement, foundIndex, searchText.length);
                } else {
                    console.error(`Could not find section: ${searchText}`);
                }
            }
        }
    });
    
    // Function to temporarily highlight a section
    function highlightSection(element, startIndex, length) {
        // Create range to select text
        const range = document.createRange();
        const textNode = element.firstChild;
        
        // Only try to select if text node exists
        if (textNode && textNode.nodeType === Node.TEXT_NODE) {
            try {
                // Select text and apply highlight style
                const tempSpan = document.createElement('span');
                tempSpan.style.backgroundColor = '#ffff99';
                tempSpan.style.transition = 'background-color 2s ease';
                
                // Try to locate exact position if possible
                // (this is approximate and may need adjustments)
                range.setStart(textNode, startIndex);
                range.setEnd(textNode, startIndex + length);
                
                // Wrap selected text
                range.surroundContents(tempSpan);
                
                // Remove highlight after 2 seconds
                setTimeout(() => {
                    tempSpan.style.backgroundColor = 'transparent';
                    // After transition, restore normal text
                    setTimeout(() => {
                        const parent = tempSpan.parentNode;
                        while (tempSpan.firstChild) {
                            parent.insertBefore(tempSpan.firstChild, tempSpan);
                        }
                        parent.removeChild(tempSpan);
                    }, 2000);
                }, 1000);
            } catch (e) {
                console.warn("Could not highlight exact section", e);
            }
        }
    }
}); 
