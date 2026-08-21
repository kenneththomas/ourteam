document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.employee-picker').forEach(picker => {
        const input = picker.querySelector('input[type="text"]');
        const hidden = picker.querySelector('input[type="hidden"]');
        const suggestions = [...picker.querySelectorAll('.employee-suggestion')];
        let visible = suggestions;
        let activeIndex = -1;

        const hide = () => { picker.querySelector('.employee-suggestions').hidden = true; activeIndex = -1; };
        const filter = () => {
            const query = input.value.toLowerCase();
            visible = suggestions.filter(option => option.dataset.name.toLowerCase().includes(query));
            suggestions.forEach(option => { option.hidden = !visible.includes(option); option.classList.remove('is-active'); });
            picker.querySelector('.employee-suggestions').hidden = visible.length === 0;
            activeIndex = -1;
        };
        const choose = option => {
            input.value = option.dataset.name;
            hidden.value = option.dataset.employeeId;
            input.setCustomValidity('');
            hide();
        };

        suggestions.forEach(option => option.addEventListener('click', () => choose(option)));
        input.addEventListener('input', () => { hidden.value = ''; input.setCustomValidity(''); filter(); });
        input.addEventListener('focus', filter);
        input.addEventListener('keydown', event => {
            if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
                event.preventDefault();
                if (!visible.length) return;
                activeIndex = (activeIndex + (event.key === 'ArrowDown' ? 1 : -1) + visible.length) % visible.length;
                suggestions.forEach(option => option.classList.remove('is-active'));
                visible[activeIndex].classList.add('is-active');
            } else if (event.key === 'Enter' && activeIndex >= 0) {
                event.preventDefault();
                choose(visible[activeIndex]);
            } else if (event.key === 'Escape') hide();
        });
        picker.closest('form')?.addEventListener('submit', event => {
            if (input.value && !hidden.value) {
                event.preventDefault();
                input.setCustomValidity('Choose a manager from the suggestions.');
                input.reportValidity();
            }
        });
        document.addEventListener('click', event => { if (!event.target.closest('.employee-picker')) hide(); });
    });
});
