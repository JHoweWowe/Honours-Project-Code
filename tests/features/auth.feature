Feature: Authentication
  As a student user
  I want to sign in and sign out
  So that I can identify myself and access personalised features

  Background:
    Given the database is seeded with test recipes

  Scenario: Unauthenticated user sees sign in link
    When I visit the homepage
    Then the page contains "Sign In with Google"
    And the page does not contain "Sign Out"

  Scenario: Authenticated user sees their display name
    Given I am logged in as a test user
    When I visit the homepage as a logged in user
    Then the response status is 200
    And the page contains "Test User"
    And the page contains "Sign Out"
    And the page does not contain "Sign In with Google"

  Scenario: Sign out clears session and returns to unauthenticated state
    Given I am logged in as a test user
    When I sign out
    Then the response status is 200
    And the page contains "Sign In with Google"
    And the page does not contain "Sign Out"

  Scenario: Sign out clears the remember-me cookie
    Given I am logged in with remember me enabled
    When I sign out
    Then the response status is 200
    And the page contains "Sign In with Google"
    And the page does not contain "Sign Out"

  Scenario: Login route redirects authenticated users to homepage
    Given I am logged in as a test user
    When I visit the login page while authenticated
    Then the response status is 302
