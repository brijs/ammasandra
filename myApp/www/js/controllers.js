angular.module('starter.controllers', ['starter.services'])


// ==================================== App ====================================
.controller('AppCtrl', function($scope, $auth) {
  
})


// ================================== Profile ==================================
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
        $scope.jwtToken = $auth.getToken();
        $scope.decodedJwtToken = JSON.stringify($auth.getPayload(), null, "   ");
        $scope.rawUser = JSON.stringify(data, null, "   ");
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


// ================================== REST API ==================================
.controller('RestAPICtrl', function($scope, $auth, $http) {
    $scope.api  = {};
    

  $scope.reset = function () {
    console.log("reset");
    $scope.api.url = "/api/v1/users/me";
    $scope.api.httpMethod = "GET";
    $scope.api.queryString = "";
    $scope.api.status = 200;
    $scope.api.response = "N/A";
    $scope.jwtToken =  $auth.getToken();
  };
  
  function getApiUrlWithParams() {
    return $scope.api.url + 
        ($scope.api.queryString? "?" + $scope.api.queryString: "")
  }

  $scope.submit = function() {
    
    // POST
    if ($scope.api.httpMethod.toUpperCase() == "POST") {
      $scope.api.httpMethod.toUpperCase = "POST";
      var postData = {};
      $scope.api.postData.replace(
          new RegExp("([^?=&]+)(=([^&]*))?", "g"),
          function($0, $1, $2, $3) { postData[$1] = $3; });
      console.log(postData);
      res = $http.post(getApiUrlWithParams(), postData);
    }
    // GET
    else {
      $scope.api.httpMethod.toUpperCase = "GET";
      res = $http.get(getApiUrlWithParams());
    }

    res
      .success(function(data, status) {
        $scope.api.status = status;
        $scope.api.response = JSON.stringify(data, null, "   ");
    })
      .error(function(data,status) {
        $scope.api.status = status;
        $scope.api.response = JSON.stringify(data, null, "   ");
      });
    
      
  };

  $scope.reset();

})


;


