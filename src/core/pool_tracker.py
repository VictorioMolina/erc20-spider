"""
Pool tracking system for Uniswap V2 and V3 pools.
Maintains state for monitored pools including liquidity status.
"""

from datetime import datetime
from typing import Dict, Optional


# todo - Check

class PoolTracker:
    """
    Tracks Uniswap pools involving the monitored token.
    Maintains liquidity and activity state for each pool.
    """

    def __init__(self):
        """Initialise empty pool dictionary."""
        self.pools: Dict[str, Dict] = {}

    def add_pool(
        self,
        pool_address: str,
        token0: str,
        token1: str,
        version: str
    ) -> None:
        """
        Add new pool to tracking system.
        
        Args:
            pool_address: Pool contract address
            token0: First token in pair
            token1: Second token in pair
            version: Pool version (V2 or V3)
        """
        key = pool_address.lower()
        self.pools[key] = {
            "address": pool_address,
            "token0": token0,
            "token1": token1,
            "version": version,
            "has_liquidity": False,
            "first_mint": None,
            "first_swap": None,
            "created_at": datetime.now(),
        }

    def get_pool_info(self, pool_address: str) -> Optional[Dict]:
        """
        Retrieve information for specified pool.
        
        Args:
            pool_address: Pool contract address
            
        Returns:
            Pool information dictionary or None
        """
        return self.pools.get(pool_address.lower())

    def mark_liquidity_added(
        self,
        pool_address: str,
        tx_hash: str,
        amount0: float,
        amount1: float
    ) -> None:
        """
        Update pool state after liquidity addition.
        
        Args:
            pool_address: Pool receiving liquidity
            tx_hash: Transaction hash
            amount0: Amount of token0 added
            amount1: Amount of token1 added
        """
        pool = self.get_pool_info(pool_address)

        if pool:
            pool["has_liquidity"] = True

            if not pool["first_mint"]:
                pool["first_mint"] = tx_hash

    def mark_first_swap(
        self,
        pool_address: str,
        tx_hash: str
    ) -> bool:
        """
        Mark first swap in pool if not already recorded.
        
        Args:
            pool_address: Pool where swap occurred
            tx_hash: Transaction hash
            
        Returns:
            True if this was the first swap
        """
        pool = self.get_pool_info(pool_address)

        if pool and not pool["first_swap"]:
            pool["first_swap"] = tx_hash
            return True

        return False
