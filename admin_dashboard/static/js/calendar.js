// calendar.js
document.addEventListener('DOMContentLoaded', function() {
    const daysElement = document.getElementById('days');
    const monthNameElement = document.getElementById('month-name');
    const yearElement = document.getElementById('year');
    const currentDate = new Date();

    // Fetch the event dates passed from Flask
    const eventDates = JSON.parse(document.getElementById('eventDates').textContent);

    // Function to render the calendar
    function renderCalendar(date) {
        const currentYear = date.getFullYear();
        const currentMonth = date.getMonth();
        const firstDayOfMonth = new Date(currentYear, currentMonth, 1).getDay();
        const lastDateOfMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
        
        monthNameElement.textContent = date.toLocaleString('default', { month: 'long' });
        yearElement.textContent = currentYear;

        daysElement.innerHTML = "";

        // Add empty slots for the days before the first day of the month
        for (let i = 0; i < firstDayOfMonth; i++) {
            daysElement.innerHTML += '<div></div>';
        }

        // Populate the days
        for (let day = 1; day <= lastDateOfMonth; day++) {
            const dayElement = document.createElement('div');
            dayElement.classList.add('day');
            dayElement.textContent = day;

            // Check if the current date has an event
            const dateString = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            if (eventDates.includes(dateString)) {
                dayElement.classList.add('event-day'); // Add the highlight class for event dates
            }

            daysElement.appendChild(dayElement);
        }
    }

    // Initial render
    renderCalendar(currentDate);

    // Navigation for previous and next months
    document.getElementById('prev').onclick = function() {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar(currentDate);
    };

    document.getElementById('next').onclick = function() {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar(currentDate);
    };
});
