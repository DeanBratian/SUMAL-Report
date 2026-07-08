# CHECKED

from core.models import DepozitDataModel

class DepositDataController:
    def __init__(self, initial_data: list[DepozitDataModel]):
        # List of DepozitDataModel with price values empty
        self.initial_data: list[DepozitDataModel] = initial_data
        # List of DepozitDataModel populated when user saves
        self.deposit_data_storage: list[DepozitDataModel] = []

    # ---------------------------------------------------------------------- #

    def get_initial_data(self) -> list[DepozitDataModel]:
        """Returns initial data to be displayed in the table in deposit data window"""
        return self.initial_data
    
    # ---------------------------------------------------------------------- #

    def save_data(self, table_data: list[DepozitDataModel]):
        """Saves data after user populates prices. Might be partial save, any save is ok"""
        self.deposit_data_storage = table_data

    # ---------------------------------------------------------------------- #

    def get_saved_data(self) -> list[DepozitDataModel]:
        """Returns the saved deposit data"""
        return self.deposit_data_storage
