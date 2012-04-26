define [
  'chaplin/mediator', 'chaplin/view',
  'text!templates/login.hbs'
], (mediator, View, template) ->
  'use strict'

  class LoginView extends View

    autoRender: true
    containerSelector: '#dialogs'
    id: 'login'
    className: 'modal fade'
    @template = template

    initialize: (options) ->
      super

      for serviceProviderName, serviceProvider of options.serviceProviders
        console.log "LoginView", serviceProviderName

        buttonSelector = ".#{serviceProviderName}"

        loginHandler = _(@loginWith).bind(
          this, serviceProviderName, serviceProvider
        )

        @delegate 'click', buttonSelector, loginHandler

    loginWith: (serviceProviderName, serviceProvider, e) ->
      @preventDefault(e)
      return unless serviceProvider.isLoaded()

      if serviceProviderName is 'custom'
        @loginData = @serializeForm @$el.find('form')

      mediator.publish 'login:pickService', serviceProviderName
      mediator.publish '!login', serviceProviderName, @loginData

      console.debug "LoginView#loginWith",
        serviceProviderName, serviceProvider