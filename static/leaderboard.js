function updateLeaderboard() {
    $.ajax({
        url: '/get_leaderboard_data', // Flask route to get JSON data
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            // Clear existing table data
            $(".leaderboard tr:not(:first)").remove();

            // Add new data to the table and animate changes
            data.employees.forEach(function(employee, index) {
                // Determine the direction of movement and add appropriate arrow
                let movement = "";
                let movementClass = "";
                let positionsMoved = Math.abs(employee.previous_position - (index + 1)); // Calculate positions moved
                if (employee.previous_position > index + 1) {
                    movement = `<span style='color: green;'>&uarr; ${positionsMoved}</span>`; // Up arrow for moving up
                    movementClass = "row-up";
                } else if (employee.previous_position < index + 1) {
                    movement = `<span style='color: red;'>&darr; ${positionsMoved}</span>`; // Down arrow for moving down
                    movementClass = "row-down";
                } else {
                    movement = "<span style='color: gray;'>&ndash;</span>"; // Dash for no movement
                }
            
                $(".leaderboard").append(
                    `<tr class="${movementClass}">
                        <td>${index + 1}</td>
                        <td><a href="/employee/${employee.id}">${employee.name}</a></td>
                        <td>${employee.xp}</td>
                        <td>${movement}</td>
                    </tr>`
                );
            });
        },
        error: function(error) {
            console.log("Error updating leaderboard: ", error);
            // Implement strategy to handle errors (e.g., retry with a longer interval)
        }
    });
}

// leaderboard update interval
setInterval(updateLeaderboard, 30000); 