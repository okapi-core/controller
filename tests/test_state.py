from okapictl.state import read_state, write_state


def test_state_round_trip(tmp_path):
    path = tmp_path / "state.json"
    write_state(path, {"bundle_version": "0.0.5"})
    assert read_state(path) == {"bundle_version": "0.0.5"}
