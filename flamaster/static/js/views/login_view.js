// Generated by CoffeeScript 1.3.1
var __hasProp = {}.hasOwnProperty,
  __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; };

define(['chaplin/mediator', 'chaplin/view', 'text!templates/login.hbs'], function(mediator, View, template) {
  'use strict';

  var LoginView;
  return LoginView = (function(_super) {

    __extends(LoginView, _super);

    LoginView.name = 'LoginView';

    function LoginView() {
      return LoginView.__super__.constructor.apply(this, arguments);
    }

    LoginView.prototype.autoRender = true;

    LoginView.prototype.containerSelector = '#dialogs';

    LoginView.prototype.id = 'login';

    LoginView.prototype.className = 'modal fade';

    LoginView.template = template;

    LoginView.prototype.initialize = function(options) {
      var buttonSelector, loginHandler, serviceProvider, serviceProviderName, _ref, _results;
      LoginView.__super__.initialize.apply(this, arguments);
      _ref = options.serviceProviders;
      _results = [];
      for (serviceProviderName in _ref) {
        serviceProvider = _ref[serviceProviderName];
        console.log("LoginView", serviceProviderName);
        buttonSelector = "." + serviceProviderName;
        loginHandler = _(this.loginWith).bind(this, serviceProviderName, serviceProvider);
        _results.push(this.delegate('click', buttonSelector, loginHandler));
      }
      return _results;
    };

    LoginView.prototype.loginWith = function(serviceProviderName, serviceProvider, e) {
      this.preventDefault(e);
      if (!serviceProvider.isLoaded()) {
        return;
      }
      if (serviceProviderName === 'custom') {
        this.loginData = this.serializeForm(this.$el.find('form'));
      }
      mediator.publish('login:pickService', serviceProviderName);
      mediator.publish('!login', serviceProviderName, this.loginData);
      return console.debug("LoginView#loginWith", serviceProviderName, serviceProvider);
    };

    return LoginView;

  })(View);
});
