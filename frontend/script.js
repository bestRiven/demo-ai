document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const predictBtn = document.getElementById('predict-btn');
    const citySelect = document.getElementById('city-select');
    
    const resultContainer = document.getElementById('result-container');
    const predictionContent = document.getElementById('prediction-content');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');

    const resultCity = document.getElementById('result-city');
    const resultImage = document.getElementById('result-image');
    const resultAqi = document.getElementById('result-aqi');
    const resultCategory = document.getElementById('result-category');
    const resultAdvice = document.getElementById('result-advice');

    // --- API Configuration ---
    const API_BASE_URL = 'http://127.0.0.1:5000';

    // --- Event Listeners ---
    predictBtn.addEventListener('click', handlePrediction);

    // --- Functions ---
    async function handlePrediction() {
        // 1. Show loader and hide previous results/errors
        showLoading(true);
        showError(null);
        predictionContent.classList.add('hidden');
        resultContainer.classList.remove('hidden');

        const city = citySelect.value;
        
        try {
            // 2. Fetch data from the backend API
            const response = await fetch(`${API_BASE_URL}/api/predict/${city}`);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // 3. Update the UI with the received data
            updateUI(data);

        } catch (error) {
            // 4. Show error message if fetch fails
            console.error('Fetch error:', error);
            showError(`无法获取预测结果: ${error.message}`);
        } finally {
            // 5. Hide loader
            showLoading(false);
        }
    }

    function updateUI(data) {
        resultCity.textContent = `城市: ${data.city}`;
        
        // 直接使用后端返回的根相对路径
        resultImage.src = data.image_url; 
        
        resultAqi.textContent = data.predicted_aqi;
        resultCategory.textContent = data.category;
        resultAdvice.textContent = data.health_advice;
        
        // Set color based on category
        const color = getCategoryColor(data.category);
        resultAqi.style.color = color;
        resultCategory.style.color = color;

        predictionContent.classList.remove('hidden');
    }

    function showLoading(isLoading) {
        if (isLoading) {
            loader.classList.remove('hidden');
        } else {
            loader.classList.add('hidden');
        }
    }

    function showError(message) {
        if (message) {
            errorMessage.textContent = message;
            errorMessage.classList.remove('hidden');
        } else {
            errorMessage.classList.add('hidden');
        }
    }

    function getCategoryColor(category) {
        switch (category) {
            case 'Good': return '#28a745';
            case 'Moderate': return '#ffc107';
            case 'Unhealthy for Sensitive Groups': return '#fd7e14';
            case 'Unhealthy': return '#dc3545';
            case 'Very Unhealthy': return '#842029';
            case 'Hazardous': return '#38161b';
            default: return 'var(--primary-color)';
        }
    }
}); 