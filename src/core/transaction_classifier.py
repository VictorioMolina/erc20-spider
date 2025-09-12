"""
Transaction classification system for transfers and liquidity events.
Identifies transaction types and assesses liquidity quality.
"""

from typing import Dict, Optional, Tuple

from utils.config import (
    MIN_LIQUIDITY_THRESHOLD,
    DEX_ROUTERS,
    CEX_ADDRESSES,
    ZERO_ADDRESS,
    BURN_ADDRESS,
)


# todo - Check

class TransactionClassifier:
    """
    Classifies blockchain transactions involving the monitored token.
    Identifies transfer types, exchange interactions, and pool activities.
    """

    def __init__(self, contract_address: str):
        """Initialise with monitored contract address."""
        self.contract_address = contract_address.lower()

    def classify_transaction_type(
        self,
        from_addr: str,
        to_addr: str,
        pool_info: Optional[Dict] = None
    ) -> Tuple[str, str]:
        """
        Classify transfer based on addresses and context.
        
        Args:
            from_addr: Source address
            to_addr: Destination address
            pool_info: Related pool information if applicable
            
        Returns:
            Tuple of (transaction type with emoji, description)
        """
        from_lower = from_addr.lower()
        to_lower = to_addr.lower()

        if from_lower == ZERO_ADDRESS.lower():
            return "🖨️ TOKEN MINT", "New tokens minted"

        if to_lower in [ZERO_ADDRESS.lower(), BURN_ADDRESS.lower()]:
            return "🔥 TOKEN BURN", "Tokens burned"
        
        if pool_info:
            if pool_info.get("has_liquidity"):
                return "🏊 POOL ACTIVITY", "Pool trading activity"
            return "🏖️ POOL SETUP", "Pool initialisation"
        
        if from_lower in DEX_ROUTERS or to_lower in DEX_ROUTERS:
            return "🔄 DEX SWAP", "DEX swap executed"
        
        if from_lower in CEX_ADDRESSES:
            return "🏦 CEX WITHDRAW", "Withdrawal from CEX"
        
        if to_lower in CEX_ADDRESSES:
            return "🏦 CEX DEPOSIT", "Deposit to CEX"
        
        return "🔄 TRANSFER", "Default transfer"

    def find_related_pool(
        self,
        from_addr: str,
        to_addr: str,
        pool_tracker
    ) -> Optional[Dict]:
        """
        Find pool related to transfer addresses.
        
        Args:
            from_addr: Source address
            to_addr: Destination address
            pool_tracker: PoolTracker instance
            
        Returns:
            Related pool info or None
        """
        from_lower = from_addr.lower()
        to_lower = to_addr.lower()
        
        for pool_info in pool_tracker.pools.values():
            if pool_info["address"].lower() in [from_lower, to_lower]:
                return pool_info
        
        return None

    def assess_liquidity_quality(
        self,
        token_amount: float
    ) -> Tuple[str, str, str]:
        """
        Assess quality of added liquidity.
        
        Args:
            token_amount: Amount of monitored token added
            
        Returns:
            Tuple of (status emoji, status text, tradeable text)
        """
        if token_amount >= MIN_LIQUIDITY_THRESHOLD:
            return (
                "🟢",
                "Substantial",
                "✅ Trading viable"
            )
        
        return (
            "🟡",
            "Minimal",
            "⚠️ Trading possible but limited"
        )

    def is_contract_involved(self, token0: str, token1: str) -> bool:
        """
        Check if monitored contract is in pool.
        
        Args:
            token0: First token
            token1: Second token
            
        Returns:
            True if monitored contract is involved
        """
        return (
            token0.lower() == self.contract_address or
            token1.lower() == self.contract_address
        )
