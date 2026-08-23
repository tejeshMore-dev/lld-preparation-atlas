from models.enums import SplitType
from strategies.equal_split_strategy import EqualSplitStrategy
from strategies.exact_split_strategy import ExactSplitStrategy
from strategies.percentage_split_strategy import PercentageSplitStrategy
from strategies.split_strategy import SplitStrategy


class SplitStrategyFactory:
    _strategies: dict[SplitType, SplitStrategy] = {
        SplitType.EQUAL: EqualSplitStrategy(),
        SplitType.EXACT: ExactSplitStrategy(),
        SplitType.PERCENTAGE: PercentageSplitStrategy(),
    }

    @classmethod
    def get_strategy(cls, split_type: SplitType) -> SplitStrategy:
        try:
            return cls._strategies[split_type]
        except KeyError as error:
            raise ValueError(f"Unsupported split type: {split_type}") from error
