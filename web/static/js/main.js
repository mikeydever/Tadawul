/**
 * Main JavaScript for the Tadawul Golden Cross Alert web interface
 */

// DOM Elements
const triggerScanButton = document.getElementById('trigger-scan');
const scanStatusElement = document.getElementById('scan-status');
const tabButtons = document.querySelectorAll('.tab-button');
const tabContents = document.querySelectorAll('.tab-content');
const viewDetailsButtons = document.querySelectorAll('.view-details');
const stockModal = document.getElementById('stock-modal');
const closeModalButton = document.querySelector('.close-modal');
const modalTitle = document.getElementById('modal-title');
const modalContent = document.getElementById('modal-content');
let stockChart = null;
let rsiChart = null;
let macdChart = null;
let stochasticChart = null;

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            switchTab(tabId);
        });
    });

    // Trigger scan button
    if (triggerScanButton) {
        triggerScanButton.addEventListener('click', triggerScan);
    }

    // View details buttons
    viewDetailsButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const stockElement = e.target.closest('[data-symbol]');
            const symbol = stockElement.getAttribute('data-symbol');
            openStockModal(symbol);
        });
    });

    // Close modal
    if (closeModalButton) {
        closeModalButton.addEventListener('click', closeModal);
    }

    // Close modal when clicking outside
    window.addEventListener('click', (e) => {
        if (e.target === stockModal) {
            closeModal();
        }
    });

    // Poll for scan status if a scan is in progress
    checkScanStatus();
});

/**
 * Switch between tabs
 * @param {string} tabId - The ID of the tab to switch to
 */
function switchTab(tabId) {
    // Update tab buttons
    tabButtons.forEach(button => {
        if (button.getAttribute('data-tab') === tabId) {
            button.classList.add('active');
        } else {
            button.classList.remove('active');
        }
    });

    // Update tab contents
    tabContents.forEach(content => {
        if (content.id === tabId) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

/**
 * Trigger a new scan
 */
async function triggerScan() {
    try {
        triggerScanButton.disabled = true;
        scanStatusElement.innerHTML = '<p class="status scanning">Starting scan...</p>';

        const response = await fetch('/api/scan', {
            method: 'POST',
        });
        const data = await response.json();

        if (data.status === 'success') {
            scanStatusElement.innerHTML = '<p class="status scanning">Scan in progress...</p>';
            // Start polling for scan status
            pollScanStatus();
        } else {
            scanStatusElement.innerHTML = `<p class="status error">Error: ${data.message}</p>`;
            triggerScanButton.disabled = false;
        }
    } catch (error) {
        console.error('Error triggering scan:', error);
        scanStatusElement.innerHTML = '<p class="status error">Error starting scan. Please try again.</p>';
        triggerScanButton.disabled = false;
    }
}

/**
 * Poll for scan status
 */
function pollScanStatus() {
    const pollInterval = setInterval(async () => {
        try {
            const response = await fetch('/api/results');
            const data = await response.json();

            if (!data.is_scanning) {
                // Scan completed
                clearInterval(pollInterval);
                triggerScanButton.disabled = false;
                
                // Refresh the page to show new results
                window.location.reload();
            }
        } catch (error) {
            console.error('Error polling scan status:', error);
            // Continue polling even if there's an error
        }
    }, 2000); // Poll every 2 seconds
}

/**
 * Check if a scan is in progress on page load
 */
function checkScanStatus() {
    fetch('/api/results')
        .then(response => response.json())
        .then(data => {
            if (data.is_scanning) {
                triggerScanButton.disabled = true;
                scanStatusElement.innerHTML = '<p class="status scanning">Scan in progress...</p>';
                pollScanStatus();
            }
        })
        .catch(error => {
            console.error('Error checking scan status:', error);
        });
}

/**
 * Open the stock details modal
 * @param {string} symbol - The stock symbol
 */
async function openStockModal(symbol) {
    modalTitle.textContent = `Loading details for ${symbol}...`;
    modalContent.innerHTML = '<div class="loading">Loading stock data...</div>';
    stockModal.style.display = 'block';

    try {
        const response = await fetch(`/api/stock/${symbol}`);
        const data = await response.json();

        if (data.status === 'success') {
            modalTitle.textContent = `Stock Details: ${symbol}`;
            
            // Create content
            let statusHtml = '';
            if (data.is_golden_cross) {
                statusHtml = '<p class="status success">Golden Cross Detected!</p>';
            } else if (data.is_approaching_cross) {
                statusHtml = '<p class="status warning">Approaching Golden Cross</p>';
            } else {
                statusHtml = '<p class="status">No Golden Cross Detected</p>';
            }

            modalContent.innerHTML = `
                <div class="stock-details">
                    ${statusHtml}
                    <p>Latest data available as of ${data.chart_data[data.chart_data.length - 1].Date}</p>
                </div>
            `;

            // Make sure the indicators-container is visible
            document.querySelector('.indicators-container').style.display = 'block';

            // Create chart
            createStockChart(data.chart_data, symbol);
        } else {
            modalContent.innerHTML = `<p class="error">Error: ${data.message}</p>`;
        }
    } catch (error) {
        console.error('Error fetching stock details:', error);
        modalContent.innerHTML = '<p class="error">Error loading stock data. Please try again.</p>';
    }
}

/**
 * Create a chart for the stock data
 * @param {Array} chartData - The chart data
 * @param {string} symbol - The stock symbol
 */
function createStockChart(chartData, symbol) {
    // Destroy existing charts if they exist
    if (stockChart) {
        stockChart.destroy();
    }
    if (rsiChart) {
        rsiChart.destroy();
    }
    if (macdChart) {
        macdChart.destroy();
    }
    if (stochasticChart) {
        stochasticChart.destroy();
    }

    const ctx = document.getElementById('stock-chart').getContext('2d');
    
    // Extract data for the chart
    const dates = chartData.map(item => item.Date);
    const prices = chartData.map(item => item.Close);
    
    // Extract SMA data if available
    const shortSmaKey = `SMA_${50}`; // Using 50 as default, should match settings
    const longSmaKey = `SMA_${200}`; // Using 200 as default, should match settings
    
    // Check if SMA data is available
    const hasSmaData = chartData.length > 0 &&
                      shortSmaKey in chartData[0] &&
                      longSmaKey in chartData[0];
    
    // Map SMA data, handling null/undefined values
    const shortSma = hasSmaData ?
        chartData.map(item => item[shortSmaKey] !== null ? item[shortSmaKey] : null) :
        [];
    const longSma = hasSmaData ?
        chartData.map(item => item[longSmaKey] !== null ? item[longSmaKey] : null) :
        [];

    // Create the chart
    stockChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dates,
            datasets: [
                {
                    label: `${symbol} Price`,
                    data: prices,
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    borderWidth: 2,
                    fill: false,
                    tension: 0.1
                },
                ...(shortSma.length > 0 ? [{
                    label: '50-Day SMA',
                    data: shortSma,
                    borderColor: '#2ecc71',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }] : []),
                ...(longSma.length > 0 ? [{
                    label: '200-Day SMA',
                    data: longSma,
                    borderColor: '#e74c3c',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }] : [])
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: false
                }
            },
            plugins: {
                tooltip: {
                    mode: 'index',
                    intersect: false
                },
                legend: {
                    position: 'top'
                }
            }
        }
    });

    // Create RSI Chart
    const rsiCtx = document.getElementById('rsi-chart').getContext('2d');
    const hasRsiData = chartData.length > 0 && 'RSI' in chartData[0];
    
    if (hasRsiData) {
        const rsiData = chartData.map(item => item.RSI !== null ? item.RSI : null);
        
        rsiChart = new Chart(rsiCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'RSI',
                    data: rsiData,
                    borderColor: '#9b59b6',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    pointRadius: 0,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        beginAtZero: false,
                        min: 0,
                        max: 100,
                        grid: {
                            color: function(context) {
                                if (context.tick.value === 30 || context.tick.value === 70) {
                                    return '#e74c3c';
                                }
                                return '#e1e4e8';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }

    // Create MACD Chart
    const macdCtx = document.getElementById('macd-chart').getContext('2d');
    const hasMacdData = chartData.length > 0 &&
                        'MACD' in chartData[0] &&
                        'MACD_Signal' in chartData[0] &&
                        'MACD_Histogram' in chartData[0];
    
    if (hasMacdData) {
        const macdLine = chartData.map(item => item.MACD !== null ? item.MACD : null);
        const macdSignal = chartData.map(item => item.MACD_Signal !== null ? item.MACD_Signal : null);
        const macdHistogram = chartData.map(item => item.MACD_Histogram !== null ? item.MACD_Histogram : null);
        
        macdChart = new Chart(macdCtx, {
            type: 'bar',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'MACD Histogram',
                        data: macdHistogram,
                        backgroundColor: function(context) {
                            const value = context.dataset.data[context.dataIndex];
                            return value >= 0 ? '#2ecc71' : '#e74c3c';
                        },
                        barPercentage: 0.8,
                        categoryPercentage: 1.0,
                        order: 3
                    },
                    {
                        label: 'MACD Line',
                        data: macdLine,
                        borderColor: '#3498db',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false,
                        type: 'line',
                        order: 1
                    },
                    {
                        label: 'Signal Line',
                        data: macdSignal,
                        borderColor: '#e74c3c',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false,
                        type: 'line',
                        order: 2
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }

    // Create Stochastic Oscillator Chart
    const stochCtx = document.getElementById('stochastic-chart').getContext('2d');
    const hasStochData = chartData.length > 0 &&
                         'Stoch_K' in chartData[0] &&
                         'Stoch_D' in chartData[0];
    
    if (hasStochData) {
        const stochK = chartData.map(item => item.Stoch_K !== null ? item.Stoch_K : null);
        const stochD = chartData.map(item => item.Stoch_D !== null ? item.Stoch_D : null);
        
        stochasticChart = new Chart(stochCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: '%K',
                        data: stochK,
                        borderColor: '#3498db',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    },
                    {
                        label: '%D',
                        data: stochD,
                        borderColor: '#e74c3c',
                        backgroundColor: 'transparent',
                        borderWidth: 2,
                        pointRadius: 0,
                        fill: false
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        beginAtZero: false,
                        min: 0,
                        max: 100,
                        grid: {
                            color: function(context) {
                                if (context.tick.value === 20 || context.tick.value === 80) {
                                    return '#e74c3c';
                                }
                                return '#e1e4e8';
                            }
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                }
            }
        });
    }
}

/**
 * Close the stock details modal
 */
function closeModal() {
    stockModal.style.display = 'none';
    // Hide the indicators container
    document.querySelector('.indicators-container').style.display = 'none';
    // Destroy all charts
    if (stockChart) {
        stockChart.destroy();
        stockChart = null;
    }
    if (rsiChart) {
        rsiChart.destroy();
        rsiChart = null;
    }
    if (macdChart) {
        macdChart.destroy();
        macdChart = null;
    }
    if (stochasticChart) {
        stochasticChart.destroy();
        stochasticChart = null;
    }
}