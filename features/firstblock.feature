Feature: Create first block

  Scenario: First block and first statement
    Given the node is running
     and the WOT ID exists
     when the application is started to create the first block
     then a first block is created
     and a first statement is created
