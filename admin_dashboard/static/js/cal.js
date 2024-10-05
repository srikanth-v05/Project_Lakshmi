document.addEventListener("DOMContentLoaded", function() {
    const prevBtn = document.getElementById('prev');
    const nextBtn = document.getElementById('next');
    const monthName = document.getElementById('month-name');
    const yearDisplay = document.getElementById('year');
    const daysContainer = document.getElementById('days');

    let currentMonth = new Date().getMonth() + 1;  // Get the current month (1-based)
    let currentYear = new Date().getFullYear();

    function loadCalendar() {
        // Fetch events from the Flask backend
        fetch(`/get_event_counts?month=${currentMonth}&year=${currentYear}`)
            .then(response => response.json())
            .then(data => {
                // Populate calendar with days and events
                daysContainer.innerHTML = '';  // Clear previous days
                for (let i = 1; i <= 31; i++) {
                    let dayDiv = document.createElement('div');
                    dayDiv.textContent = i;
                    
                    // Highlight if event count exists for this day
                    if (data[i]) {
                        dayDiv.classList.add('has-event');  // Add a special class for styling
                    }
                    daysContainer.appendChild(dayDiv);
                }
                monthName.textContent = getMonthName(currentMonth);
                yearDisplay.textContent = currentYear;
            });
    }

    function getMonthName(month) {
        const monthNames = ["January", "February", "March", "April", "May", "June",
                            "July", "August", "September", "October", "November", "December"];
        return monthNames[month - 1];
    }

    // Event listeners for navigating months
    prevBtn.addEventListener('click', function() {
        currentMonth--;
        if (currentMonth < 1) {
            currentMonth = 12;
            currentYear--;
        }
        loadCalendar();
    });

    nextBtn.addEventListener('click', function() {
        currentMonth++;
        if (currentMonth > 12) {
            currentMonth = 1;
            currentYear++;
        }
        loadCalendar();
    });

    // Initial load
    loadCalendar();
});
