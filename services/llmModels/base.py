from abc import ABC, abstractmethod


class BaseLLMService(ABC):
    @abstractmethod
    async def get_sql_query_with_database_structure(
        self, database_structure: str, order: str
    ) -> str:
        pass

    @abstractmethod
    async def get_result_interpretation(self, result: str, order: str) -> str:
        pass

    @abstractmethod
    async def optimize_generate(self, query: str, database_structure: str) -> str:
        pass

    @abstractmethod
    async def create_database(self, database_structure: str) -> str:
        pass

    @abstractmethod
    async def populate_database(
        self, creation_command: str, number_insertions: int
    ) -> str:
        pass

    @abstractmethod
    def analyze_optimization_effects(
        self,
        original_metrics: dict,
        optimized_metrics: dict,
        original_query: str,
        optimized_query: str,
        applied_indexes: list,
    ) -> str:
        pass

    @abstractmethod
    async def get_weights(self, ram_gb: int = None, priority: str = None) -> str:
        pass
