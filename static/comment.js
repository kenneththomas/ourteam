$(document).ready(function(){
    $('#comment-form').on('submit', function(event){
        event.preventDefault();
        $.ajax({
            url: $(this).attr('action'),
            method: 'post',
            data: $(this).serialize(),
            success: function(response){
                // Append the new comment to the comment list
                $('.wall').append(response);
            }
        });
    });
});
