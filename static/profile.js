document.addEventListener('DOMContentLoaded', () => {
    const wall = document.querySelector('#profile-wall');
    const commentForm = document.querySelector('#comment-form');
    const friendForm = document.querySelector('#add-friend-form');

    commentForm?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const response = await fetch(commentForm.action, { method: 'POST', body: new FormData(commentForm) });
        if (response.ok) {
            const html = await response.text();
            wall.insertAdjacentHTML('afterbegin', html);
            commentForm.querySelector('textarea').value = '';
        }
    });

    document.addEventListener('click', async (event) => {
        const button = event.target.closest('.delete-comment');
        if (!button || !confirm('Delete this message?')) return;
        const response = await fetch(`/delete_comment/${button.dataset.commentId}`, { method: 'POST' });
        if (response.ok) button.closest('.wall-message, .comment-container')?.remove();
    });

    friendForm?.addEventListener('submit', async (event) => {
        event.preventDefault();
        const friendId = document.querySelector('#friend-id').value;
        const body = new URLSearchParams({ friend_id: friendId });
        const response = await fetch(`/employee/${window.ourTeamProfile.employeeId}/add_friend`, { method: 'POST', body });
        const result = await response.json();
        alert(result.success ? `${result.friend_name} is now an ally.` : result.message);
        if (result.success) location.reload();
    });

    const dialog = document.querySelector('#media-dialog');
    const image = dialog?.querySelector('img');
    const video = dialog?.querySelector('video');
    let current = null;
    document.querySelectorAll('.media-tile').forEach(tile => tile.addEventListener('click', () => {
        current = tile.dataset;
        const isImage = current.kind === 'image';
        image.hidden = !isImage;
        video.hidden = isImage;
        if (isImage) image.src = current.url;
        else { video.src = current.url; video.play(); }
        dialog.querySelector('p').textContent = current.caption || 'Untitled artifact';
        dialog.querySelector('#set-profile-picture').hidden = !isImage;
        dialog.showModal();
    }));
    dialog?.querySelector('.dialog-close')?.addEventListener('click', () => { video.pause(); dialog.close(); });
    dialog?.querySelector('#set-profile-picture')?.addEventListener('click', async () => {
        const body = new URLSearchParams({ employee_id: window.ourTeamProfile.employeeId, image_url: current.url });
        if ((await fetch('/set_profile_picture', { method: 'POST', body })).ok) location.reload();
    });
    dialog?.querySelector('#delete-media')?.addEventListener('click', async () => {
        if (!confirm('Delete this artifact?')) return;
        const response = await fetch(`/delete_${current.kind}/${current.id}`, { method: 'POST' });
        if (response.ok) location.reload();
    });
});
