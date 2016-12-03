Feature: Testing the Participants class only.

  Scenario: A first participant is added.
    Given there are no participants
     when a participant is added
     then a block is found.
