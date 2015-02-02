angular.module('starter.controllers', ['starter.services'])

.controller('AppCtrl', function($scope, $auth) {
  
})


.controller('ProfileCtrl', function($scope, $alert, $auth, Account) {
  $scope.logout = function() {
    $auth.logout();
    $scope.isAuthenticated = $auth.isAuthenticated();
    $scope.getProfile();
  };


  $scope.getProfile = function() {
    Account.getProfile()
      .success(function(data) {
        $scope.user = data;
        $scope.jwtToken = $auth.getToken() + " Decoded: " 
        + JSON.stringify($auth.getPayload(), null, '\t');
        $scope.rawUser = JSON.stringify(data, null, '\t');
      })
      .error(function(error) {
        $alert({
          content: error.messgae,
          animation: 'fadeZoomFadeDown',
          type: 'material',
          duration: 3
        });
      });
  };

  $scope.authenticate = function(provider) {
    $auth.authenticate(provider)
    .then(function() {
      $scope.isAuthenticated = $auth.isAuthenticated();
      $scope.getProfile();
      $alert({
        content: 'You have successfully logged in',
        animation: 'fadeZoomFadeDown',
        type: 'material',
        duration: 3
      });
    })
    .catch(function(response) {
      $alert({
        content: response.data ? response.data.message : response,
        animation: 'fadeZoomFadeDown',
        type: 'material',
        duration: 3
      });
    });
  };

  $scope.isAuthenticated = $auth.isAuthenticated();
  $scope.getProfile();
})

;


