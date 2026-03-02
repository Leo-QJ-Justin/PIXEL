"""Tests for PetStateMachine."""


from src.core.pet_state import PetState, PetStateMachine


class TestPetStateMachine:
    def test_initial_state_is_idle(self):
        sm = PetStateMachine()
        assert sm.state == PetState.IDLE

    def test_custom_initial_state(self):
        sm = PetStateMachine(PetState.SLEEPING)
        assert sm.state == PetState.SLEEPING

    def test_valid_transition_idle_to_wandering(self):
        sm = PetStateMachine()
        assert sm.transition(PetState.WANDERING) is True
        assert sm.state == PetState.WANDERING

    def test_valid_transition_idle_to_sleeping(self):
        sm = PetStateMachine()
        assert sm.transition(PetState.SLEEPING) is True
        assert sm.state == PetState.SLEEPING

    def test_valid_transition_idle_to_alerting(self):
        sm = PetStateMachine()
        assert sm.transition(PetState.ALERTING) is True
        assert sm.state == PetState.ALERTING

    def test_invalid_transition_wandering_to_sleeping(self):
        sm = PetStateMachine()
        sm.transition(PetState.WANDERING)
        assert sm.transition(PetState.SLEEPING) is False
        assert sm.state == PetState.WANDERING

    def test_invalid_transition_sleeping_to_wandering(self):
        sm = PetStateMachine()
        sm.transition(PetState.SLEEPING)
        assert sm.transition(PetState.WANDERING) is False
        assert sm.state == PetState.SLEEPING

    def test_alerting_can_only_go_to_idle(self):
        sm = PetStateMachine()
        sm.transition(PetState.ALERTING)
        assert sm.transition(PetState.WANDERING) is False
        assert sm.transition(PetState.SLEEPING) is False
        assert sm.transition(PetState.IDLE) is True
        assert sm.state == PetState.IDLE

    def test_wandering_can_be_interrupted_by_alert(self):
        sm = PetStateMachine()
        sm.transition(PetState.WANDERING)
        assert sm.transition(PetState.ALERTING) is True
        assert sm.state == PetState.ALERTING

    def test_sleeping_can_be_interrupted_by_alert(self):
        sm = PetStateMachine()
        sm.transition(PetState.SLEEPING)
        assert sm.transition(PetState.ALERTING) is True
        assert sm.state == PetState.ALERTING

    def test_transition_to_same_state_succeeds(self):
        sm = PetStateMachine()
        assert sm.transition(PetState.IDLE) is True
        assert sm.state == PetState.IDLE

    def test_force_bypasses_rules(self):
        sm = PetStateMachine()
        sm.transition(PetState.ALERTING)
        sm.force(PetState.SLEEPING)  # normally invalid
        assert sm.state == PetState.SLEEPING

    def test_is_idle_property(self):
        sm = PetStateMachine()
        assert sm.is_idle is True
        sm.transition(PetState.WANDERING)
        assert sm.is_idle is False

    def test_is_busy_property(self):
        sm = PetStateMachine()
        assert sm.is_busy is False

        sm.transition(PetState.ALERTING)
        assert sm.is_busy is True

        sm.force(PetState.WANDERING)
        assert sm.is_busy is True

        sm.force(PetState.SLEEPING)
        assert sm.is_busy is True

        sm.force(PetState.REACTING)
        assert sm.is_busy is True

    def test_state_changed_signal(self, qtbot):
        sm = PetStateMachine()
        signals = []
        sm.state_changed.connect(lambda old, new: signals.append((old, new)))

        sm.transition(PetState.WANDERING)
        assert len(signals) == 1
        assert signals[0] == (PetState.IDLE, PetState.WANDERING)

    def test_no_signal_on_same_state_transition(self, qtbot):
        sm = PetStateMachine()
        signals = []
        sm.state_changed.connect(lambda old, new: signals.append((old, new)))

        sm.transition(PetState.IDLE)
        assert len(signals) == 0
