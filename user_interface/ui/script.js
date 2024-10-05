// Toggle Chatbox visibility
const chatbotIcon = document.getElementById('chatbot-icon');
const chatbox = document.getElementById('chatbox');
const closeChatbox = document.querySelector('.close-chatbox');

chatbotIcon.addEventListener('click', () => {
    chatbox.classList.toggle('d-none');
});

closeChatbox.addEventListener('click', () => {
    chatbox.classList.add('d-none');
});
