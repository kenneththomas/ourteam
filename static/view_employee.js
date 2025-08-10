$(document).ready(function() {
    $('.delete-comment').click(function() {
        var commentId = $(this).data('comment-id');
        if (confirm('Are you sure you want to delete this comment?')) {
            $.ajax({
                url: '/delete_comment/' + commentId,
                type: 'POST',
                success: function(result) {
                    $('#comment-' + commentId).remove();
                },
                error: function(error) {
                    console.log('Error:', error);
                }
            });
        }
    });

    // Image modal functions
    function showImageModal(imageUrl, caption) {
        $('#imageModal').css('display', 'block');
        $('#fullImage').attr('src', imageUrl);
        $('#caption').text(caption);
        window.currentImageUrl = imageUrl;
        $('#setProfilePictureButton').css('display', 'block');
    }

    function showModal(imageUrl, caption) {
        showImageModal(imageUrl, caption);
    }

    function closeModal() {
        $('#imageModal').css('display', 'none');
        $('#setProfilePictureButton').css('display', 'none');
    }

    // Video modal functions
    function showVideoModal(videoUrl, caption) {
        $('#videoModal').css('display', 'block');
        $('#videoSource').attr('src', videoUrl);
        $('#fullVideo')[0].load();
        $('#videoCaption').text(caption);
    }

    function closeVideoModal() {
        $('#videoModal').css('display', 'none');
        $('#fullVideo')[0].pause();
        $('#videoSource').attr('src', '');
    }

    // Close the modal when clicking anywhere outside the image or video
    $(window).click(function(event) {
        if (event.target.id === 'imageModal') {
            $('#imageModal').css('display', 'none');
            $('#setProfilePictureButton').css('display', 'none');
        }
        if (event.target.id === 'videoModal') {
            closeVideoModal();
        }
    });

    function setProfilePicture() {
        $.ajax({
            type: 'POST',
            url: '/set_profile_picture',
            data: {
                'employee_id': employeeId, // Make sure to define employeeId in your template
                'image_url': window.currentImageUrl
            },
            success: function(response) {
                alert('Profile picture updated successfully.');
                location.reload();
            },
            error: function(error) {
                alert('An error occurred while updating the profile picture.');
            }
        });
    }

    // Add friend form submission
    $('#add-friend-form').submit(function(e) {
        e.preventDefault();
        var friendId = $('#friend-id').val();
        
        $.ajax({
            url: "/employee/" + employeeId + "/add_friend",
            method: 'POST',
            data: { friend_id: friendId },
            success: function(response) {
                if (response.success) {
                    $('#friends-list').append('<li><a href="/employee/' + friendId + '">' + response.friend_name + '</a></li>');
                    $('#friend-id').val('');
                    alert('Friend added successfully! You are now friends with ' + response.friend_name + '.');
                } else {
                    alert(response.message);
                }
            },
            error: function(xhr, status, error) {
                alert('An error occurred while adding friend: ' + xhr.responseText);
            }
        });
    });

    // Expose functions to global scope
    window.showModal = showModal;
    window.closeModal = closeModal;
    window.showImageModal = showImageModal;
    window.showVideoModal = showVideoModal;
    window.closeVideoModal = closeVideoModal;
    window.setProfilePicture = setProfilePicture;
});