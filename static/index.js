function updateUsersList() {
    // Make an AJAX request to the update_users_list route
    fetch("/update_users_list")
        .then(function(response) {
            if (response.ok) {
                location.reload();
                return response.text(); 
            } else {
                throw new Error("Error updating users list");
            }
        })
        .then(function(message) {
            alert(message);
        })
        .catch(function(error) {
            alert(error.message);
        });
}

function updateUserGroupsList() {
    // Make an AJAX request to the update_users_list route
    fetch("/update_user_groups_list")
        .then(function(response) {
            if (response.ok) {
                location.reload();
                return response.text(); 
            } else {
                throw new Error("Error updating user groups list");
            }
        })
        .then(function(message) {
            alert(message);
        })
        .catch(function(error) {
            alert(error.message);
        });
}

