const memoryTextarea = document.getElementById('memory');
const charCount = document.getElementById('memoryCount');
const form = document.getElementById('lyricsForm');
const submitBtn = document.getElementById('submitBtn');
const errorMessage = document.getElementById('errorMessage');

// Character counter
if (memoryTextarea && charCount) {
    memoryTextarea.addEventListener('input', function() {
        const length = this.value.length;
        charCount.textContent = `${length} characters`;
        
        if (length > 500) {
            charCount.style.color = '#ff4444';
        } else {
            charCount.style.color = '#ff69b4';
        }
    });
}

// Form submission
if (form) {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const btnText = submitBtn.querySelector('.btn-text');
        const btnLoader = submitBtn.querySelector('.btn-loader');
        
        errorMessage.style.display = 'none';
        
        submitBtn.disabled = true;
        btnText.style.display = 'none';
        btnLoader.style.display = 'inline-block';
        
        try {
            const formData = new FormData(form);
            
            const response = await fetch('/generate-form', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                window.location.href = data.redirect;
            } else {
                throw new Error(data.error || 'Generation failed');
            }
            
        } catch (error) {
            errorMessage.textContent = error.message || 'An error occurred. Please try again.';
            errorMessage.style.display = 'block';
            
            submitBtn.disabled = false;
            btnText.style.display = 'inline-block';
            btnLoader.style.display = 'none';
            
            errorMessage.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

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
