/**
 * dashboard.js - Dashboard functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle date filter changes
    const dateFilterButtons = document.querySelectorAll('.btn-group[role="group"] .btn');
    
    dateFilterButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Visual feedback while loading new data
            const dashboard = document.querySelector('main.container');
            if (dashboard) {
                dashboard.style.opacity = '0.7';
                dashboard.style.transition = 'opacity 0.3s';
            }
        });
    });
    
    // Prepare tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Responsive behavior for activity cards
    adjustActivityCards();
    window.addEventListener('resize', adjustActivityCards);
});

/**
 * Adjusts activity cards layout based on screen size
 */
function adjustActivityCards() {
    const activityList = document.querySelector('.activity-list');
    
    if (activityList) {
        // Adjust max height based on screen size
        if (window.innerWidth < 768) {
            activityList.style.maxHeight = '400px';
        } else {
            activityList.style.maxHeight = '500px';
        }
    }
}

/**
 * Creates text percentages for time in different heart rate zones
 * @param {Object} zonePercentages - Object with zone names as keys and percentages as values
 * @param {Object} zoneColors - Object with zone names as keys and color codes as values
 * @param {string} containerId - ID of the container element
 */
function createZoneProgressBar(zonePercentages, zoneColors, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    // Clear previous content
    container.innerHTML = '';
    
    // Create a container for zone percentages
    const zoneContainer = document.createElement('div');
    zoneContainer.className = 'd-flex gap-2 flex-wrap';
    
    // Add colored percentages for each zone
    for (const [zone, percentage] of Object.entries(zonePercentages)) {
        if (percentage > 0) {
            const zoneElement = document.createElement('div');
            zoneElement.style.color = zoneColors[zone];
            zoneElement.style.fontWeight = 'bold';
            zoneElement.textContent = `${Math.round(percentage)}%`;
            zoneElement.setAttribute('data-bs-toggle', 'tooltip');
            zoneElement.setAttribute('data-bs-placement', 'top');
            zoneElement.setAttribute('title', `${zone}: ${percentage}%`);
            
            zoneContainer.appendChild(zoneElement);
        }
    }
    
    container.appendChild(zoneContainer);
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(container.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}
