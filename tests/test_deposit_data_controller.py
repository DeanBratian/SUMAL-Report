import pytest
from controllers.deposit_data_controller import DepositDataController
from tests.conftest import make_deposit_data

@pytest.fixture
def initial_deposits():
    return [
        make_deposit_data(name = "Dep A", tip = "Depozit Temporar LR"),
        make_deposit_data(name = "Dep B", tip = "Depozit")
    ]

# ---------------------------------------------------------------------- #

class TestInitialization:

    def test_stores_initial_data(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        assert ctrl.initial_data == initial_deposits

    # ---------------------------------------------------------------------- #

    def test_storage_starts_empty(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        assert ctrl.get_saved_data() == []

    # ---------------------------------------------------------------------- #

    def test_empty_initial_data(self):
        ctrl = DepositDataController([])
        assert ctrl.initial_data == []

# ---------------------------------------------------------------------- #

class TestGetInitialData:

    def test_returns_initial_data(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        result = ctrl.get_initial_data()
        assert result is ctrl.initial_data
        assert len(result) == 2

    # ---------------------------------------------------------------------- #

    def test_returns_same_reference(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        assert ctrl.get_initial_data() is ctrl.get_initial_data()

# ---------------------------------------------------------------------- #

class TestSaveData:

    def test_save_stores_data(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        updated = [
            make_deposit_data(name = "Dep A", tip = "Depozit Temporar LR", p_intrare_lr_mc = 100),
            make_deposit_data(name = "Dep B", tip = "Depozit")
        ]
        ctrl.save_data(updated)
        assert ctrl.get_saved_data() == updated

    # ---------------------------------------------------------------------- #

    def test_save_overwrites_previous(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        first = [
            make_deposit_data(name = "Dep A", tip = "Depozit Temporar LR", p_intrare_lr_mc = 50),
            make_deposit_data(name = "Dep B", tip = "Depozit")
        ]
        second = [
            make_deposit_data(name = "Dep A", tip = "Depozit Temporar LR", p_intrare_lr_mc = 200),
            make_deposit_data(name = "Dep B", tip = "Depozit", p_intrare_lr_mc = 300)
        ]
        ctrl.save_data(first)
        ctrl.save_data(second)
        assert ctrl.get_saved_data() == second

    # ---------------------------------------------------------------------- #

    def test_save_empty_list(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        ctrl.save_data([])
        assert ctrl.get_saved_data() == []

    # ---------------------------------------------------------------------- #

    def test_save_does_not_modify_initial_data(self, initial_deposits):
        ctrl = DepositDataController(initial_deposits)
        ctrl.save_data([
            make_deposit_data(name = "Dep A", tip = "Depozit Temporar LR", p_intrare_lr_mc = 999),
            make_deposit_data(name = "Dep B", tip = "Depozit", p_intrare_lr_mc = 888)
        ])
        assert len(ctrl.initial_data) == 2
        assert ctrl.initial_data[0].nume_depozit == "Dep A"
        assert ctrl.initial_data[0].price_data.p_intrare_lr_mc == 0
