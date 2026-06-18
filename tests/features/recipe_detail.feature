Feature: Recipe Detail Page
  As a student user
  I want to view a full recipe
  So that I can follow the ingredients and directions

  Background:
    Given the database is seeded with test recipes

  Scenario: Recipe detail page loads
    When I view the recipe with id "507f1f77bcf86cd799439011"
    Then the response status is 200

  Scenario: Recipe title is displayed
    When I view the recipe with id "507f1f77bcf86cd799439011"
    Then the page contains "Simple Pasta Bolognese"

  Scenario: Ingredients section is displayed
    When I view the recipe with id "507f1f77bcf86cd799439011"
    Then the page contains "Ingredients"

  Scenario: Directions section is displayed
    When I view the recipe with id "507f1f77bcf86cd799439011"
    Then the page contains "Directions"

  Scenario: Price section is displayed
    When I view the recipe with id "507f1f77bcf86cd799439011"
    Then the page contains "Pricing"

  Scenario: Related recipes of the same cuisine are displayed
    When I view the recipe with id "507f1f77bcf86cd799439011"
    Then the page contains "Italian Pizza Margherita"

  Scenario: Nonexistent recipe id returns 200 with empty page
    When I view the recipe with id "000000000000000000000099"
    Then the response status is 200
