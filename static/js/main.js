
// Mobile Menu Toggle
const mobileMenuToggle = document.getElementById('mobileMenuToggle');
const navbar = document.getElementById('navbar');
const menuOverlay = document.getElementById('menuOverlay');
const body = document.body;

function toggleMenu() {
    navbar.classList.toggle('active');
    menuOverlay.classList.toggle('active');
    body.style.overflow = navbar.classList.contains('active') ? 'hidden' : '';

    const icon = mobileMenuToggle.querySelector('i');
    if (navbar.classList.contains('active')) {
        icon.classList.remove('fa-bars');
        icon.classList.add('fa-times');
    } else {
        icon.classList.remove('fa-times');
        icon.classList.add('fa-bars');
    }
}

if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', toggleMenu);
}

// Close menu when clicking overlay
if (menuOverlay) {
    menuOverlay.addEventListener('click', toggleMenu);
}

// Close menu on link click
const navLinks = document.querySelectorAll('.nav-link');
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        if (window.innerWidth <= 768 && navbar.classList.contains('active')) {
            toggleMenu();
        }
    });
});

// Close menu on window resize
let resizeTimer;
window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => {
        if (window.innerWidth > 768 && navbar.classList.contains('active')) {
            toggleMenu();
        }
    }, 250);
});

// Alert messages auto-close
const alerts = document.querySelectorAll('.alert');
alerts.forEach(alert => {
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => alert.remove(), 300);
        });
    }

    // Auto close after 5 seconds
    setTimeout(() => {
        if (alert && alert.parentElement) {
            alert.style.opacity = '0';
            alert.style.transform = 'translateX(100%)';
            setTimeout(() => alert.remove(), 300);
        }
    }, 5000);
});

// Back to Top Button
const backToTop = document.getElementById('backToTop');

window.addEventListener('scroll', () => {
    if (window.pageYOffset > 300) {
        backToTop.classList.add('show');
    } else {
        backToTop.classList.remove('show');
    }
});

if (backToTop) {
    backToTop.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Navbar background change on scroll
let lastScroll = 0;
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    const currentScroll = window.pageYOffset;

    if (window.innerWidth > 768) {
        if (currentScroll > 100) {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
            navbar.style.backdropFilter = 'blur(10px)';
        }
    }

    lastScroll = currentScroll;
});

// Form validation
const forms = document.querySelectorAll('form');
forms.forEach(form => {
    form.addEventListener('submit', (e) => {
        const requiredInputs = form.querySelectorAll('[required]');
        let isValid = true;

        requiredInputs.forEach(input => {
            if (!input.value.trim()) {
                isValid = false;
                input.style.borderColor = '#e74c3c';

                // Show error message
                let errorMsg = input.parentElement.querySelector('.error-message');
                if (!errorMsg) {
                    errorMsg = document.createElement('small');
                    errorMsg.className = 'error-message';
                    errorMsg.style.color = '#e74c3c';
                    errorMsg.style.fontSize = '0.75rem';
                    errorMsg.style.marginTop = '0.25rem';
                    errorMsg.style.display = 'block';
                    input.parentElement.appendChild(errorMsg);
                }
                errorMsg.textContent = 'This field is required';

                // Add shake animation
                input.classList.add('shake');
                setTimeout(() => input.classList.remove('shake'), 500);
            } else {
                input.style.borderColor = '#e2e8f0';
                const errorMsg = input.parentElement.querySelector('.error-message');
                if (errorMsg) errorMsg.remove();
            }
        });

        if (!isValid) {
            e.preventDefault();
        }
    });
});

// Real-time validation
const inputs = document.querySelectorAll('input, textarea, select');
inputs.forEach(input => {
    input.addEventListener('input', () => {
        if (input.hasAttribute('required') && input.value.trim()) {
            input.style.borderColor = '#e2e8f0';
            const errorMsg = input.parentElement.querySelector('.error-message');
            if (errorMsg) errorMsg.remove();
        }
    });
});

// Newsletter form submission
const newsletterForm = document.getElementById('newsletterForm');
if (newsletterForm) {
    newsletterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const emailInput = newsletterForm.querySelector('input[type="email"]');
        const email = emailInput.value.trim();

        if (email && isValidEmail(email)) {
            // Show success message
            showNotification('Thank you for subscribing!', 'success');
            emailInput.value = '';
        } else {
            showNotification('Please enter a valid email address', 'error');
        }
    });
}

// Email validation helper
function isValidEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// Notification system
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-slide-in`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
        <span>${message}</span>
        <button class="alert-close">&times;</button>
    `;

    const flashMessages = document.querySelector('.flash-messages');
    if (flashMessages) {
        flashMessages.appendChild(notification);

        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        }, 3000);

        // Close button functionality
        const closeBtn = notification.querySelector('.alert-close');
        closeBtn.addEventListener('click', () => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => notification.remove(), 300);
        });
    }
}

// Add CSS animation for shake
const style = document.createElement('style');
style.textContent = `
    @keyframes shake {
        0%, 100% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
    }
    .shake {
        animation: shake 0.3s ease;
    }
`;
document.head.appendChild(style);

// Detect touch devices
const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
if (isTouchDevice) {
    document.body.classList.add('touch-device');
}

// Lazy load images
const images = document.querySelectorAll('img[data-src]');
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            observer.unobserve(img);
        }
    });
});

images.forEach(img => imageObserver.observe(img));

// Prevent zoom on double tap (for better mobile UX)
let lastTouchEnd = 0;
document.addEventListener('touchend', (e) => {
    const now = Date.now();
    if (now - lastTouchEnd <= 300) {
        e.preventDefault();
    }
    lastTouchEnd = now;
}, false);
