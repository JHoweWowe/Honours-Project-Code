Feature: Time String Converter
  As a developer
  I want the scraper helper to parse cooking-time strings
  So that recipe durations are stored as integers correctly

  Scenario: Convert minutes-only string
    When I convert the time string "30 mins"
    Then the converted minutes are 30

  Scenario: Convert hours-only string with short form
    When I convert the time string "2 hrs"
    Then the converted minutes are 120

  Scenario: Convert hours and minutes combined
    When I convert the time string "1 hr 15 mins"
    Then the converted minutes are 75

  Scenario: Convert singular hour
    When I convert the time string "1 hour"
    Then the converted minutes are 60

  Scenario: Convert long-form minutes
    When I convert the time string "45 minutes"
    Then the converted minutes are 45

  Scenario: Convert plural hours long form
    When I convert the time string "2 hours"
    Then the converted minutes are 120
