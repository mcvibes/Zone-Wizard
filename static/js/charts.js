/**
 * charts.js - Helper functions for Chart.js visualizations
 */

// Configure Chart.js global defaults
if (Chart) {
    // Set default font family and colors
    Chart.defaults.font.family = "'Helvetica Neue', 'Helvetica', 'Arial', sans-serif";
    
    // Adjust colors for dark theme
    Chart.defaults.color = '#e0e0e0';
    
    // Remove chart backgrounds
    Chart.defaults.plugins.legend.labels.boxWidth = 15;
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
    
    // Enable responsive charts by default
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
}

/**
 * Creates a heart rate zone chart
 * @param {string} elementId - Canvas element ID
 * @param {Array} labels - Zone labels
 * @param {Array} data - Zone percentages
 * @param {Array} colors - Zone colors
 */
function createZoneChart(elementId, labels, data, colors) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 15
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.label}: ${context.raw}%`;
                        }
                    }
                }
            }
        }
    });
}

/**
 * Creates a heart rate time series chart
 * @param {string} elementId - Canvas element ID
 * @param {Array} timeData - Time values in seconds
 * @param {Array} heartRateData - Heart rate values
 * @param {Object} zones - Zone thresholds
 * @param {Object} zoneColors - Zone colors
 */
function createHeartRateChart(elementId, timeData, heartRateData, zones, zoneColors) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Format time labels
    const labels = timeData.map(seconds => {
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const mins = minutes % 60;
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}h ${mins.toString().padStart(2, '0')}m`;
        } else {
            return `${mins}:${secs.toString().padStart(2, '0')}`;
        }
    });
    
    // Create datasets
    const datasets = [
        {
            label: 'Heart Rate',
            data: heartRateData,
            borderColor: '#FF6384',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
            fill: true,
            tension: 0.1
        }
    ];
    
    // Add zone thresholds if available
    if (zones) {
        for (const [zoneName, thresholds] of Object.entries(zones)) {
            datasets.push({
                label: zoneName,
                data: Array(timeData.length).fill(thresholds.max),
                borderColor: zoneColors[zoneName],
                borderDash: [5, 5],
                borderWidth: 1,
                pointRadius: 0,
                fill: false
            });
        }
    }
    
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            scales: {
                x: {
                    ticks: {
                        autoSkip: true,
                        maxTicksLimit: 10
                    },
                    title: {
                        display: true,
                        text: 'Time'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Heart Rate (bpm)'
                    },
                    suggestedMin: 60,
                    suggestedMax: 190
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        filter: function(item) {
                            // Only show Heart Rate in legend
                            return item.text === 'Heart Rate';
                        }
                    }
                }
            }
        }
    });
}
