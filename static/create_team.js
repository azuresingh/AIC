$(document).ready(function() {
            // Fetch assignment groups from ServiceNow API and populate the dropdown
            var username = "admin"; // Replace with your ServiceNow username
            var password = "-yKbnJXi28H%"; // Replace with your ServiceNow password
            var assignmentGroupDropdown = $('#assignment_group');

            $.ajax({
                url: "https://dev79652.service-now.com/api/now/table/sys_user_group",
                method: "GET",
                headers: {
                    "Authorization": "Basic " + btoa(username + ":" + password)
                },
                success: function(response) {
                    var groups = response.result;
                    populateDropdown(groups, assignmentGroupDropdown);
                },
                error: function(error) {
                    console.error('Failed to fetch assignment groups:', error);
                }
            });

    // Fetch users and user groups from the server
            var fetchUsers = $.ajax({
                url: '/users', // Replace with the appropriate route in your Flask app
                method: 'GET'
            });

            var fetchUserGroups = $.ajax({
                url: '/user_groups', // Replace with the appropriate route in your Flask app
                method: 'GET'
            });

            Promise.all([fetchUsers, fetchUserGroups])
                .then(function(responses) {
                    var users = responses[0].users;
                    var userGroups = responses[1].user_groups;

                    populateDropdown(users, $('#team_lead'));
                    populateDropdown(userGroups, assignmentGroupDropdown);
                })
                .catch(function(error) {
                    console.error('Failed to fetch data:', error);
                });

            function populateDropdown(data, dropdown) {
                dropdown.empty().append($('<option>').text('Select').val(''));

                data.forEach(function(item) {
                    dropdown.append($('<option>').text(item.name).val(item.sys_id));
                });
            }
        });