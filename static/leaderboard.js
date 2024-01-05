let previousData = null;

function updateLeaderboard() {
    $.ajax({
        url: '/get_leaderboard_data', // Flask route to get JSON data
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            // Convert data to a string for comparison
            let currentData = JSON.stringify(data);

            // Check if the data has changed
            if (currentData === previousData) {
                // If the data has not changed, dont do anything
                return;
            }

            // Update previousData for the next comparison
            previousData = currentData;

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

// Define your interval time in milliseconds (30000ms = 30s)
let leaderboardRefreshTime = 30000;

// Use the variable in your setInterval function
let leaderboardInterval = setInterval(updateLeaderboard, leaderboardRefreshTime);

// Function to update the interval time
function updateIntervalTime(newTime) {
    // Enforce a minimum of 5 seconds
    if (newTime < 5000) {
        console.log("Interval time cannot be less than 5 seconds.");
        return;
    }

    // Clear the existing interval
    clearInterval(leaderboardInterval);

    // Update the interval time
    leaderboardRefreshTime = newTime;

    // Set a new interval with the updated time
    leaderboardInterval = setInterval(updateLeaderboard, leaderboardRefreshTime);
}

function updateRefreshTime() {
    // Get the value from the input box
    let newTime = document.getElementById('refreshTime').value;

    // Multiply by 1000 to convert to milliseconds
    newTime *= 1000;

    // Check if the value is less than 5000
    if (newTime < 5000) {
        alert("Refresh time cannot be less than 5 seconds.");
        return;
    }

    // Call the updateIntervalTime function with the new time
    updateIntervalTime(newTime);
}