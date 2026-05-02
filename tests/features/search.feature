Feature: Recipe Search
  As a student user
  I want to search and filter recipes
  So that I can find something suitable to cook

  Background:
    Given the database is seeded with test recipes

  Scenario: Search page loads with no filters
    When I search with no filters
    Then the response status is 200

  Scenario: Search results include seeded recipe titles
    When I search with no filters
    Then the page contains "Simple Pasta Bolognese"

  Scenario: Cuisine filter returns matching recipes
    When I search with cuisine filter "Chinese"
    Then the response status is 200
    And the page contains "Quick Stir Fry"

  Scenario: Cuisine filter excludes non-matching recipes
    When I search with cuisine filter "Chinese"
    Then the page does not contain "Vegan Buddha Bowl"

  Scenario: Dietary filter returns vegan recipes
    When I search with dietary filter "Vegan"
    Then the response status is 200
    And the page contains "Vegan Buddha Bowl"

  Scenario: Time filter excludes recipes that take too long
    When I search with maximum time 20
    Then the page does not contain "Italian Pizza Margherita"

  Scenario: Sort by rating returns 200
    When I search sorted by "rating"
    Then the response status is 200

  Scenario: No matching results shows empty state message
    When I search with cuisine filter "NonexistentCuisine"
    Then the page contains "None Found"
