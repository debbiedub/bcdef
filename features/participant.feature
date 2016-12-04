Feature: Testing the Participants class only.

  Scenario: A first participant is added.
    Given there are no participants
     when a participant is added
     then a block is found
      and there is one participant

  Scenario: A second participant with the same block.
    Given one participant with a block
     when another participant is added
     then a new block is not found
      and there are two participants
