// script.js

// Function to handle the checkbox change event
function handleCheckboxChange(event) {
    // Get the user ID, field name, and value from the checkbox element
    var userId = event.target.dataset.userId;
    var field = event.target.dataset.field;
    var value = event.target.checked ? 1 : 0;

    // Send an AJAX request to update the user in the database
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/update_user');
    xhr.setRequestHeader('Content-Type', 'application/json');
    xhr.onreadystatechange = function() {
        if (xhr.readyState === XMLHttpRequest.DONE) {
            if (xhr.status === 200) {
                var response = JSON.parse(xhr.responseText);
                console.log(response.message);
            } else {
                console.error('Error:', xhr.status);
            }
        }
    };
    xhr.send(JSON.stringify({ userId: userId, field: field, value: value }));
}

// Attach the event listener to the checkboxes
var checkboxes = document.querySelectorAll('input[type="checkbox"]');
checkboxes.forEach(function(checkbox) {
    checkbox.addEventListener('change', handleCheckboxChange);
});
