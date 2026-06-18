Feature: User Profile Page
  As an authenticated user
  I want to view and update my profile
  So that the app can personalise recipe recommendations for me

  Background:
    Given the database is seeded with test recipes

  Scenario: Unauthenticated user is redirected to login
    When I visit the profile page without logging in
    Then the response status is 302

  Scenario: Authenticated user can view the profile page
    Given I am logged in as a test user
    When I visit the profile page
    Then the response status is 200
    And the page contains "My Profile"
    And the page contains "About You"
    And the page contains "Cooking Preferences"
    And the page contains "Dietary Preferences"
    And the page contains "Preferred Cuisines"

  Scenario: Profile page contains a first name input field
    Given I am logged in as a test user
    When I visit the profile page
    Then the page contains "First Name"

  Scenario: Profile page shows the user's email
    Given I am logged in as a test user
    When I visit the profile page
    Then the page contains "testuser@example.com"

  Scenario: Submitting without a first name shows an error
    Given I am logged in as a test user
    When I submit the profile form without a first name
    Then the response status is 200
    And the page contains "First name is required"

  Scenario: Valid profile save shows success message
    Given I am logged in as a test user
    When I submit a valid profile form
    Then the response status is 200
    And the page contains "Profile saved!"

  Scenario: Invalid date of birth shows an error
    Given I am logged in as a test user
    When I submit the profile form with an invalid date of birth
    Then the response status is 200
    And the page contains "Date of birth must be a valid date"

  Scenario: Max budget of zero shows an error
    Given I am logged in as a test user
    When I submit the profile form with zero budget
    Then the response status is 200
    And the page contains "Max budget must be greater than 0"

  Scenario: Household size out of range shows an error
    Given I am logged in as a test user
    When I submit the profile form with household size out of range
    Then the response status is 200
    And the page contains "Household size must be between 1 and 20"

  Scenario: Saved profile values are pre-populated on next visit
    Given I am logged in as a test user
    When I submit a valid profile form
    And I visit the profile page
    Then the page contains "Alice"
