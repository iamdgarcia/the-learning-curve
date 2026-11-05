// Document Extraction Service Frontend JavaScript

const API_BASE = '/.netlify/functions/doc-extraction';

document.addEventListener('DOMContentLoaded', () => {
    const docTypeSelect = document.getElementById('doc-type');
    const contentTextarea = document.getElementById('content');
    const fieldsInput = document.getElementById('fields');
    const extractBtn = document.getElementById('extract-btn');
    const loadingDiv = document.getElementById('loading');
    const resultsDiv = document.getElementById('results');
    
    // Metrics elements
    const totalExtractionsEl = document.getElementById('total-extractions');
    const successRateEl = document.getElementById('success-rate');
    const avgTimeEl = document.getElementById('avg-time');
    const healthStatusEl = document.getElementById('health-status');
    
    // Result elements
    const statusBadge = document.getElementById('status-badge');
    const requestIdEl = document.getElementById('request-id');
    const processingTimeEl = document.getElementById('processing-time');
    const warningsDiv = document.getElementById('warnings');
    const errorsDiv = document.getElementById('errors');
    const extractedContentEl = document.getElementById('extracted-content');
    const confidenceDiv = document.getElementById('confidence');
    const confidenceValueEl = document.getElementById('confidence-value');
    
    // Sample content for each document type
    const sampleContent = {
        invoice: `INVOICE #INV-2024-001
Date: 01/15/2024
Due Date: 02/15/2024

Vendor: Acme Corporation
123 Business Ave
New York, NY 10001

Items:
- Web Development Services: $5,000.00
- Server Hosting (1 year): $1,200.00
- Domain Registration: $50.00

Subtotal: $6,250.00
Tax (10%): $625.00
Total: $6,875.00

Payment Terms: Net 30`,
        
        receipt: `RECEIPT

Store: Tech Gadgets Inc
Date: 01/10/2024 Time: 2:30 PM

Items:
USB Cable.........$9.99
Phone Case........$24.99
Screen Protector.$14.99

Subtotal: $49.97
Tax: $4.50
Total: $54.47

Payment: Credit Card
Thank you for shopping!`,
        
        contract: `CONTRACT AGREEMENT

This Agreement is entered into as of January 1, 2024

BETWEEN:
Party A: Company Inc ("Client")
Party B: Service Provider LLC ("Provider")

TERMS:
1. Services: Web development and maintenance
2. Duration: 12 months
3. Compensation: $5,000/month
4. Effective Date: January 1, 2024
5. Termination: 30 days notice required`,
        
        resume: `JOHN DOE
Email: john.doe@email.com | Phone: (555) 123-4567

EXPERIENCE:
Senior Developer - Tech Corp (2020-Present)
- Led team of 5 developers
- Built microservices architecture

Developer - StartUp Inc (2018-2020)
- Full-stack development

EDUCATION:
BS Computer Science - University (2018)

SKILLS:
Python, JavaScript, React, AWS, Docker`
    };
    
    // Auto-fill sample content based on document type
    docTypeSelect.addEventListener('change', () => {
        const docType = docTypeSelect.value;
        if (sampleContent[docType]) {
            contentTextarea.value = sampleContent[docType];
        }
    });
    
    // Initialize with sample content
    contentTextarea.value = sampleContent.invoice;
    
    async function updateMetrics() {
        try {
            const response = await fetch(`${API_BASE}/metrics`);
            const data = await response.json();
            totalExtractionsEl.textContent = data.total_requests || 0;
            successRateEl.textContent = (data.success_rate || 100) + '%';
            avgTimeEl.textContent = Math.round(data.average_response_time_ms || 0) + 'ms';
        } catch (e) {
            console.log('Metrics not available');
        }
    }
    
    async function checkHealth() {
        try {
            const response = await fetch(`${API_BASE}/health`);
            const data = await response.json();
            healthStatusEl.textContent = data.status === 'healthy' ? 'Healthy' : 'Degraded';
            healthStatusEl.className = 'metric-value ' + (data.status === 'healthy' ? 'status-healthy' : 'status-unhealthy');
        } catch (e) {
            healthStatusEl.textContent = 'Unknown';
        }
    }
    
    async function extractDocument() {
        const docType = docTypeSelect.value;
        const content = contentTextarea.value.trim();
        let fields = fieldsInput.value.trim();
        
        if (!content) {
            alert('Please enter document content to extract');
            return;
        }
        
        // Parse fields
        const extractionFields = fields ? fields.split(',').map(f => f.trim()) : undefined;
        
        // Show loading
        extractBtn.disabled = true;
        extractBtn.textContent = 'Extracting...';
        loadingDiv.classList.remove('hidden');
        resultsDiv.classList.add('hidden');
        
        try {
            const response = await fetch(`${API_BASE}/extract`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    document_type: docType,
                    content: content,
                    content_type: 'text',
                    extraction_fields: extractionFields
                })
            });
            
            const data = await response.json();
            
            // Display results
            displayResults(data);
            
            // Update metrics
            updateMetrics();
            
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            extractBtn.disabled = false;
            extractBtn.textContent = 'Extract Data';
            loadingDiv.classList.add('hidden');
        }
    }
    
    function displayResults(data) {
        resultsDiv.classList.remove('hidden');
        
        // Status
        if (data.success) {
            statusBadge.textContent = 'Success';
            statusBadge.className = 'status-badge success';
        } else {
            statusBadge.textContent = 'Failed';
            statusBadge.className = 'status-badge error';
        }
        
        requestIdEl.textContent = `Request ID: ${data.request_id}`;
        processingTimeEl.textContent = `${data.processing_time_ms}ms`;
        
        // Warnings
        if (data.warnings && data.warnings.length > 0) {
            warningsDiv.classList.remove('hidden');
            warningsDiv.textContent = '⚠️ ' + data.warnings.join(', ');
        } else {
            warningsDiv.classList.add('hidden');
        }
        
        // Errors
        if (data.errors && data.errors.length > 0) {
            errorsDiv.classList.remove('hidden');
            errorsDiv.textContent = '❌ ' + data.errors.join(', ');
        } else {
            errorsDiv.classList.add('hidden');
        }
        
        // Extracted data
        if (data.extracted_data) {
            extractedContentEl.textContent = JSON.stringify(data.extracted_data, null, 2);
        } else {
            extractedContentEl.textContent = 'No data extracted';
        }
        
        // Confidence
        if (data.confidence !== undefined && data.confidence !== null) {
            confidenceDiv.classList.remove('hidden');
            confidenceValueEl.textContent = (data.confidence * 100).toFixed(0) + '%';
        } else {
            confidenceDiv.classList.add('hidden');
        }
    }
    
    // Event listener
    extractBtn.addEventListener('click', extractDocument);
    
    // Initial load
    updateMetrics();
    checkHealth();
    
    // Refresh metrics every 10 seconds
    setInterval(() => {
        updateMetrics();
        checkHealth();
    }, 10000);
});