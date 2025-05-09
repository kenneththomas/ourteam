document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('employeeSearch');
    const searchResults = document.getElementById('searchResults');
    let searchTimeout;

    // Add smooth scrolling to all links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Add hover effect to show more details
    document.querySelectorAll('.employee-card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.boxShadow = '0 6px 12px rgba(0, 0, 0, 0.15)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });

    // Make cards clickable to focus on that employee
    document.querySelectorAll('.employee-card').forEach(card => {
        card.addEventListener('click', function(e) {
            if (!e.target.closest('a')) {  // Don't navigate if clicking a link
                const employeeId = this.dataset.employeeId;
                window.location.href = `/org_tree/${employeeId}`;
            }
        });
    });

    // Handle search input
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();

        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        searchTimeout = setTimeout(() => {
            fetch(`/autocomplete_employee?term=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    searchResults.innerHTML = '';
                    if (data.length > 0) {
                        data.forEach(employee => {
                            const div = document.createElement('div');
                            div.className = 'search-result-item';
                            div.innerHTML = `
                                <img src="${employee.picture || '/static/resources/default_profile.png'}" alt="${employee.label}">
                                <div>
                                    <div>${employee.label}</div>
                                </div>
                            `;
                            div.addEventListener('click', () => {
                                window.location.href = `/org_tree/${employee.value}`;
                            });
                            searchResults.appendChild(div);
                        });
                        searchResults.style.display = 'block';
                    } else {
                        searchResults.style.display = 'none';
                    }
                });
        }, 300);
    });

    // Close search results when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });

    // Add click handler to expand/collapse sub-reports
    document.querySelectorAll('.report-card').forEach(card => {
        const subReports = card.nextElementSibling;
        if (subReports && subReports.classList.contains('sub-reports')) {
            card.addEventListener('click', function(e) {
                if (!e.target.closest('a')) {  // Don't toggle if clicking a link
                    subReports.classList.toggle('collapsed');
                }
            });
        }
    });
}); 