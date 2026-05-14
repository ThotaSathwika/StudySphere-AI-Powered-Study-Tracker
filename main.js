// Toast notification auto-dismiss
document.addEventListener('DOMContentLoaded', function() {
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach((toast, index) => {
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3000 + (index * 500));
    });
});

// Pomodoro Timer
class PomodoroTimer {
    constructor() {
        this.timeLeft = 25 * 60; // 25 minutes in seconds
        this.isRunning = false;
        this.interval = null;
        this.display = document.getElementById('pomodoro-display');
        this.circle = document.getElementById('pomodoro-circle');
        
        if (this.display) {
            this.updateDisplay();
        }
        
        this.setupEventListeners();
    }
    
    setupEventListeners() {
        const startBtn = document.getElementById('start-timer');
        const pauseBtn = document.getElementById('pause-timer');
        const resetBtn = document.getElementById('reset-timer');
        
        if (startBtn) {
            startBtn.addEventListener('click', () => this.start());
        }
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.pause());
        }
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.reset());
        }
    }
    
    start() {
        if (!this.isRunning) {
            this.isRunning = true;
            if (this.circle) this.circle.classList.add('active');
            this.interval = setInterval(() => {
                this.timeLeft--;
                this.updateDisplay();
                
                if (this.timeLeft <= 0) {
                    this.pause();
                    this.playAlarm();
                    alert('Pomodoro session complete! Time for a break.');
                    this.timeLeft = 5 * 60; // 5 minute break
                }
            }, 1000);
        }
    }
    
    pause() {
        this.isRunning = false;
        if (this.circle) this.circle.classList.remove('active');
        if (this.interval) {
            clearInterval(this.interval);
        }
    }
    
    reset() {
        this.pause();
        this.timeLeft = 25 * 60;
        this.updateDisplay();
    }
    
    updateDisplay() {
        if (this.display) {
            const minutes = Math.floor(this.timeLeft / 60);
            const seconds = this.timeLeft % 60;
            this.display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }
    
    playAlarm() {
        // Create audio context for alarm sound
        const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        oscillator.frequency.value = 800;
        oscillator.type = 'sine';
        gainNode.gain.value = 0.3;
        
        oscillator.start();
        setTimeout(() => oscillator.stop(), 500);
    }
}

// Initialize Pomodoro Timer
const pomodoroTimer = new PomodoroTimer();

// Chart initialization
function initCharts() {
    // Weekly Study Chart
    const weeklyCtx = document.getElementById('weeklyChart');
    if (weeklyCtx) {
        const weeklyData = JSON.parse(weeklyCtx.dataset.chart);
        new Chart(weeklyCtx, {
            type: 'line',
            data: {
                labels: Object.keys(weeklyData),
                datasets: [{
                    label: 'Study Hours',
                    data: Object.values(weeklyData),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }
    
    // Subject Distribution Chart
    const subjectCtx = document.getElementById('subjectChart');
    if (subjectCtx) {
        const subjectData = JSON.parse(subjectCtx.dataset.chart);
        new Chart(subjectCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(subjectData),
                datasets: [{
                    data: Object.values(subjectData),
                    backgroundColor: [
                        '#667eea',
                        '#f093fb',
                        '#00f5ff',
                        '#00ff87',
                        '#bf00ff',
                        '#ff00ff',
                        '#f5576c',
                        '#ffd93d'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                }
            }
        });
    }
    
    // Monthly Productivity Chart
    const monthlyCtx = document.getElementById('monthlyChart');
    if (monthlyCtx) {
        const monthlyData = JSON.parse(monthlyCtx.dataset.chart);
        new Chart(monthlyCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(monthlyData),
                datasets: [{
                    label: 'Study Hours',
                    data: Object.values(monthlyData),
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: '#667eea',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }
    
    // Daily Productivity Chart
    const dailyCtx = document.getElementById('dailyChart');
    if (dailyCtx) {
        const dailyData = JSON.parse(dailyCtx.dataset.chart);
        new Chart(dailyCtx, {
            type: 'line',
            data: {
                labels: Object.keys(dailyData),
                datasets: [{
                    label: 'Daily Hours',
                    data: Object.values(dailyData),
                    borderColor: '#00ff87',
                    backgroundColor: 'rgba(0, 255, 135, 0.2)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        labels: { color: '#ffffff' }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    },
                    y: {
                        ticks: { color: '#ffffff' },
                        grid: { color: 'rgba(255, 255, 255, 0.1)' }
                    }
                }
            }
        });
    }
}

// Initialize charts when DOM is loaded
document.addEventListener('DOMContentLoaded', initCharts);

// Smooth scroll for navigation
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});

// Add animation on scroll
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, observerOptions);

document.querySelectorAll('.glass-card, .stat-card').forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(20px)';
    card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(card);
});

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return true;
    
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            input.style.borderColor = '#f5576c';
        } else {
            input.style.borderColor = '';
        }
    });
    
    return isValid;
}

// Add event listeners for form validation
document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', function(e) {
        if (!validateForm(form.id)) {
            e.preventDefault();
            alert('Please fill in all required fields.');
        }
    });
});

// Dynamic subject colors for cards
function getSubjectColor(subject) {
    const colors = {
        'Mathematics': '#667eea',
        'Programming': '#00f5ff',
        'Science': '#00ff87',
        'AI & Machine Learning': '#bf00ff',
        'Data Structures': '#ff00ff',
        'Web Development': '#f093fb',
        'Aptitude': '#ffd93d',
        'Other': '#f5576c'
    };
    return colors[subject] || '#667eea';
}

// Export confirmation
function confirmExport() {
    return confirm('Are you sure you want to export your study data?');
}

// Delete confirmation
function confirmDelete(message) {
    return confirm(message || 'Are you sure you want to delete this item?');
}

// Update progress bars with animation
function animateProgressBars() {
    document.querySelectorAll('.progress-bar').forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0%';
        setTimeout(() => {
            bar.style.width = width;
        }, 100);
    });
}

// Initialize progress bar animation
document.addEventListener('DOMContentLoaded', animateProgressBars);
