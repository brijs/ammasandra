angular.module('starter.services', [])

.factory('Account', function($http) {
	return {
		getProfile: function() {
			return $http.get('/api/v1/users/me');
		},
		updateProfile: function(profileData) {
			// return $http.put('/api/me', profileData);
			console.log("Not Implementeed");
		}
	}

});