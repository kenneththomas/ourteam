document.addEventListener('DOMContentLoaded', () => {
    const input = document.querySelector('#employeeSearch');
    const results = document.querySelector('#searchResults');
    let timer;

    const hideResults = () => { results.classList.remove('visible'); };
    const initials = (label) => label.split('(')[0].trim().split(/\s+/).map(part => part[0]).slice(0, 2).join('');

    input?.addEventListener('input', () => {
        clearTimeout(timer);
        const term = input.value.trim();
        if (term.length < 2) return hideResults();
        timer = setTimeout(async () => {
            const response = await fetch(`/autocomplete_employee?term=${encodeURIComponent(term)}`);
            const people = await response.json();
            results.replaceChildren();
            people.forEach(person => {
                const button = document.createElement('button');
                button.type = 'button';
                const avatar = document.createElement('span');
                avatar.className = 'avatar avatar-xs avatar-tone-' + (person.value % 6);
                avatar.textContent = initials(person.label);
                const name = document.createElement('span');
                name.textContent = person.label;
                const arrow = document.createElement('b');
                arrow.textContent = '↗';
                button.append(avatar, name, arrow);
                button.addEventListener('click', () => { window.location.href = `/org_tree/${person.value}`; });
                results.append(button);
            });
            results.classList.toggle('visible', people.length > 0);
        }, 180);
    });

    document.addEventListener('click', event => {
        if (!event.target.closest('.org-search-wrap')) hideResults();
    });

    document.addEventListener('keydown', event => {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
            event.preventDefault();
            input?.focus();
        }
    });
});
