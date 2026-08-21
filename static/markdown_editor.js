document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.markdown-editor').forEach(editor => {
        const textarea = editor.querySelector('textarea');
        const preview = editor.querySelector('.markdown-preview');
        const previewToggle = editor.querySelector('.preview-toggle');

        const wrapSelection = (before, after = before, fallback = 'text') => {
            const start = textarea.selectionStart;
            const end = textarea.selectionEnd;
            const selected = textarea.value.slice(start, end) || fallback;
            textarea.setRangeText(`${before}${selected}${after}`, start, end, 'select');
            textarea.focus();
            textarea.dispatchEvent(new Event('input', { bubbles: true }));
        };

        editor.querySelectorAll('[data-markdown]').forEach(button => {
            button.addEventListener('click', () => {
                const action = button.dataset.markdown;
                if (action === 'bold') wrapSelection('**', '**');
                if (action === 'italic') wrapSelection('_', '_');
                if (action === 'link') wrapSelection('[', '](https://)', 'link text');
                if (action === 'list') {
                    const start = textarea.value.lastIndexOf('\n', textarea.selectionStart - 1) + 1;
                    const endBreak = textarea.value.indexOf('\n', textarea.selectionEnd);
                    const end = endBreak === -1 ? textarea.value.length : endBreak;
                    const lines = textarea.value.slice(start, end).split('\n').map(line => `- ${line}`).join('\n');
                    textarea.setRangeText(lines, start, end, 'select');
                    textarea.focus();
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                }
            });
        });

        previewToggle.addEventListener('click', async () => {
            const showingPreview = previewToggle.getAttribute('aria-pressed') === 'true';
            if (showingPreview) {
                preview.hidden = true;
                textarea.closest('label').hidden = false;
                previewToggle.setAttribute('aria-pressed', 'false');
                previewToggle.textContent = 'Preview';
                textarea.focus();
                return;
            }

            previewToggle.disabled = true;
            try {
                const response = await fetch(editor.dataset.previewUrl, {
                    method: 'POST',
                    body: new URLSearchParams({ content: textarea.value }),
                });
                if (!response.ok) throw new Error('Preview request failed');
                const result = await response.json();
                preview.innerHTML = result.html || '<p>Nothing to preview yet.</p>';
                textarea.closest('label').hidden = true;
                preview.hidden = false;
                previewToggle.setAttribute('aria-pressed', 'true');
                previewToggle.textContent = 'Write';
            } catch (error) {
                preview.innerHTML = '<p>Preview is temporarily unavailable.</p>';
                preview.hidden = false;
            } finally {
                previewToggle.disabled = false;
            }
        });
    });
});
