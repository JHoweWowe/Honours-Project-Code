Feature: Homepage
  As a student user
  I want to visit the homepage
  So that I can discover featured recipes and browse by cuisine

  Background:
    Given the database is seeded with test recipes

  Scenario: Homepage loads successfully
    When I visit the homepage
    Then the response status is 200

  Scenario: Featured recipes section is rendered
    When I visit the homepage
    Then the page contains "Featured Student Recipes"

  Scenario: Cuisine browser is rendered
    When I visit the homepage
    Then the page contains "Browse by Cuisine"

  Scenario: Seeded cuisine appears as a browsable pill
    When I visit the homepage
    Then the page contains "Italian"
