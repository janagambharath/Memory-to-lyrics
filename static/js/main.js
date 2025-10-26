// Character counter for memory textarea
const memoryTextarea = document.getElementById('memory');
const charCount = document.getElementById('memoryCount');

if (memoryTextarea && charCount) {
    memoryTextarea.addEventListener('input', function() {
        const length = this.value.length;
        charCount.textContent = `${length} characters`;
        
        if (length > 500) {
            charCount.style.color = '#ff4444';
        } else {
            charCount.style.color = '#999';
        }
    });
}

// Save form data to localStorage on change
const form = document.getElementById('lyricsForm');
if (form) {
    const formInputs = form.querySelectorAll('input, textarea, select');
    
    // Load saved data on page load
    formInputs.forEach(input => {
        const savedValue = localStorage.getItem(input.name);
        if (savedValue && input.type !== 'checkbox') {
            input.value = savedValue;
        } else if (input.type === 'checkbox' && savedValue === 'true') {
            input.checked = true;
        }
    });

    // Update character count if memory was loaded
    if (memoryTextarea && memoryTextarea.value) {
        charCount.textContent = `${memoryTextarea.value.length} characters`;
    }

    // Save data on change
    formInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.type === 'checkbox') {
                localStorage.setItem(this.name, this.checked);
            } else {
                localStorage.setItem(this.name, this.value);
            }
        });
    });
}

// Form submission
if (form) {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitBtn = document.getElementById('submitBtn');
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        const errorMessage = document.getElementById('errorMessage');
        
        // Hide any previous errors
        errorMessage.style.display = 'none';
        
        // Disable button and show loader
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        
        try {
            const formData = new FormData(form);
            
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Clear saved form data
                formInputs.forEach(input => {
                    localStorage.removeItem(input.name);
                });
                
                // Redirect to result page
                window.location.href = data.redirect;
            } else {
                throw new Error(data.error || 'Generation failed');
            }
            
        } catch (error) {
            // Show error message
            errorMessage.textContent = error.message || 'An error occurred. Please try again.';
            errorMessage.style.display = 'block';
            
            // Re-enable button
            submitBtn.disabled = false;
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
            
            // Scroll to error message
            errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

// Add smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Form validation hints
const requiredFields = document.querySelectorAll('[required]');
requiredFields.forEach(field => {
    field.addEventListener('invalid', function(e) {
        e.preventDefault();
        this.style.borderColor = '#ff4444';
        setTimeout(() => {
            this.style.borderColor = '';
        }, 3000);
    });
    
    field.addEventListener('input', function() {
        if (this.validity.valid) {
            this.style.borderColor = '#4caf50';
            setTimeout(() => {
                this.style.borderColor = '';
            }, 1000);
        }
    });
});
