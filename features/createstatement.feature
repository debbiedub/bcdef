Feature: Create statements

  Scenario: A new block arrives
    Given the blockchain exists
     and there are other blockchain users
     when one of the other blockchain users signal a new block
     then a new statement is created
