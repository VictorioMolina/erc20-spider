"""
Blockchain event decoder with comprehensive Uniswap support.
Handles ERC-20 transfers, pool creation, and trading events.
"""

from typing import Dict, Optional, Tuple
from web3 import Web3

from .logger import Logger
from utils.config import CONTRACT_DECIMALS, EVENT_SIGNATURES

logger = Logger().get_logger()

# todo - Check


class EventDecoder:
    """
    Event decoder for blockchain logs.
    Handles all major Uniswap and ERC-20 event types with robust error handling.
    """

    @staticmethod
    def decode_transfer(log: Dict) -> Optional[Tuple[str, str, float]]:
        """
        Decode ERC-20 Transfer event.
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (from_address, to_address, token_amount) or None
        """
        try:
            topics = log.get("topics", [])
            if len(topics) < 3:
                logger.debug("Transfer event missing required topics")
                return None
                
            # Extract addresses from indexed topics
            from_addr = "0x" + topics[1][-40:]
            to_addr = "0x" + topics[2][-40:]
            
            # Extract amount from event data
            data = log.get("data", "0x")
            if len(data) < 66:
                logger.debug("Transfer event missing amount data")
                return None
                
            amount_wei = int(data[2:], 16)
            amount_tokens = amount_wei / (10 ** CONTRACT_DECIMALS)
            
            return (
                Web3.to_checksum_address(from_addr),
                Web3.to_checksum_address(to_addr),
                amount_tokens
            )
            
        except (ValueError, IndexError) as error:
            logger.error(f"Transfer decode error: {error}")
            return None

    @staticmethod
    def decode_pair_created(log: Dict) -> Optional[Tuple[str, str, str]]:
        """
        Decode Uniswap V2 PairCreated event.
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (token0, token1, pair_address) or None
        """
        try:
            topics = log.get("topics", [])
            if len(topics) < 3:
                logger.debug("PairCreated event missing required topics")
                return None
                
            # Extract token addresses from indexed topics
            token0 = "0x" + topics[1][-40:]
            token1 = "0x" + topics[2][-40:]
            
            # Extract pair address from event data
            data = log.get("data", "")
            if len(data) < 42:
                logger.debug("PairCreated event missing pair address data")
                return None
                
            pair_address = "0x" + data[-40:]
            
            return (
                Web3.to_checksum_address(token0),
                Web3.to_checksum_address(token1),
                Web3.to_checksum_address(pair_address)
            )
            
        except (ValueError, IndexError) as error:
            logger.error(f"PairCreated decode error: {error}")
            return None

    @staticmethod
    def decode_mint_event(log: Dict) -> Optional[Tuple[float, float]]:
        """
        Decode Uniswap V2 Mint event (liquidity addition).
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (amount0, amount1) in token units or None
        """
        try:
            data = log.get("data", "0x")[2:]
            if len(data) < 128:
                logger.debug("Mint event insufficient data length")
                return None
                
            # Extract amounts (assuming 18 decimals for both tokens)
            amount0_wei = int(data[:64], 16)
            amount1_wei = int(data[64:128], 16)
            
            # Convert to token units
            amount0 = amount0_wei / (10 ** 18)
            amount1 = amount1_wei / (10 ** 18)
            
            return amount0, amount1
            
        except (ValueError, IndexError) as error:
            logger.error(f"Mint event decode error: {error}")
            return None

    @staticmethod
    def decode_mint_v3_event(log: Dict) -> Optional[Tuple[float, float]]:
        """
        Decode Uniswap V3 Mint event (liquidity addition).
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (amount0, amount1) in token units or None
        """
        try:
            topics = log.get("topics", [])
            if len(topics) < 4:
                logger.debug("V3 Mint event missing required topics")
                return None
                
            data = log.get("data", "0x")[2:]
            if len(data) < 256:
                logger.debug("V3 Mint event insufficient data length")
                return None
                
            # Skip sender and amount_liq (64-128: amount_liq)
            amount0_wei = int(data[128:192], 16)
            amount1_wei = int(data[192:256], 16)
            
            # Convert to token units assuming 18 decimals
            amount0 = amount0_wei / (10 ** 18)
            amount1 = amount1_wei / (10 ** 18)
            
            return amount0, amount1
            
        except (ValueError, IndexError) as error:
            logger.error(f"V3 Mint decode error: {error}")
            return None

    @staticmethod
    def decode_pool_created_v3(log: Dict) -> Optional[Tuple[str, str, str, int]]:
        """
        Decode Uniswap V3 PoolCreated event.
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (token0, token1, pool_address, fee) or None
        """
        try:
            topics = log.get("topics", [])
            if len(topics) < 3:
                logger.debug("V3 PoolCreated event missing required topics")
                return None
                
            # Extract token addresses from indexed topics
            token0 = "0x" + topics[1][-40:]
            token1 = "0x" + topics[2][-40:]
            
            # Extract fee and pool address from event data
            data = log.get("data", "")[2:]
            if len(data) < 128:
                logger.debug("V3 PoolCreated event insufficient data")
                return None
                
            fee = int(data[:64], 16)
            pool_address = "0x" + data[88:128]
            
            return (
                Web3.to_checksum_address(token0),
                Web3.to_checksum_address(token1),
                Web3.to_checksum_address(pool_address),
                fee
            )
            
        except (ValueError, IndexError) as error:
            logger.error(f"V3 PoolCreated decode error: {error}")
            return None

    @staticmethod
    def decode_swap_v2_event(log: Dict) -> Optional[Tuple[str, str, int, int, int, int]]:
        """
        Decode Uniswap V2 Swap event.
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (sender, to, amount0_in, amount1_in, amount0_out, amount1_out) or None
        """
        try:
            topics = log.get("topics", [])
            if len(topics) < 3:
                logger.debug("V2 Swap event missing required topics")
                return None
                
            # Extract addresses from indexed topics
            sender = "0x" + topics[1][-40:]
            to = "0x" + topics[2][-40:]
            
            # Extract swap amounts from event data
            data = log.get("data", "0x")[2:]
            if len(data) < 256:
                logger.debug("V2 Swap event insufficient data length")
                return None
                
            amount0_in = int(data[:64], 16)
            amount1_in = int(data[64:128], 16)
            amount0_out = int(data[128:192], 16)
            amount1_out = int(data[192:256], 16)
            
            return (
                Web3.to_checksum_address(sender),
                Web3.to_checksum_address(to),
                amount0_in,
                amount1_in,
                amount0_out,
                amount1_out
            )
            
        except (ValueError, IndexError) as error:
            logger.error(f"V2 Swap decode error: {error}")
            return None

    @staticmethod
    def decode_swap_v3_event(log: Dict) -> Optional[Tuple[str, str, int, int, int, int]]:
        """
        Decode Uniswap V3 Swap event.
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (sender, recipient, amount0, amount1, sqrt_price_x96, liquidity) or None
        """
        try:
            topics = log.get("topics", [])
            if len(topics) < 3:
                logger.debug("V3 Swap event missing required topics")
                return None
                
            # Extract addresses from indexed topics
            sender = "0x" + topics[1][-40:]
            recipient = "0x" + topics[2][-40:]
            
            # Extract swap data (V3 has different structure than V2)
            data = log.get("data", "0x")[2:]
            if len(data) < 256:
                logger.debug("V3 Swap event insufficient data length")
                return None
                
            # V3 swap amounts can be negative (represented as two's complement)
            amount0_raw = int(data[:64], 16)
            amount1_raw = int(data[64:128], 16)
            sqrt_price_x96 = int(data[128:192], 16)
            liquidity = int(data[192:256], 16)
            
            # Convert from signed integers if needed
            amount0 = amount0_raw if amount0_raw < 2**255 else amount0_raw - 2**256
            amount1 = amount1_raw if amount1_raw < 2**255 else amount1_raw - 2**256
            
            return (
                Web3.to_checksum_address(sender),
                Web3.to_checksum_address(recipient),
                abs(amount0),  # Use absolute values for simplicity
                abs(amount1),
                sqrt_price_x96,
                liquidity
            )
            
        except (ValueError, IndexError) as error:
            logger.error(f"V3 Swap decode error: {error}")
            return None

    @staticmethod
    def decode_burn_event(log: Dict) -> Optional[Tuple[float, float]]:
        """
        Decode Uniswap V2 Burn event (liquidity removal).
        
        Args:
            log: Raw event log data
            
        Returns:
            Tuple of (amount0, amount1) in token units or None
        """
        try:
            data = log.get("data", "0x")[2:]
            if len(data) < 128:
                logger.debug("Burn event insufficient data length")
                return None
                
            # Extract amounts (similar to mint event)
            amount0_wei = int(data[:64], 16)
            amount1_wei = int(data[64:128], 16)
            
            # Convert to token units
            amount0 = amount0_wei / (10 ** 18)
            amount1 = amount1_wei / (10 ** 18)
            
            return amount0, amount1
            
        except (ValueError, IndexError) as error:
            logger.error(f"Burn event decode error: {error}")
            return None


class EventSignatureValidator:
    """
    Event signature validation for efficient event filtering.
    Provides fast signature matching for all supported event types.
    """

    @staticmethod
    def is_transfer_event(signature: str) -> bool:
        """Check if signature matches ERC-20 Transfer event."""
        return signature == EVENT_SIGNATURES["Transfer"]

    @staticmethod
    def is_pair_created_event(signature: str) -> bool:
        """Check if signature matches Uniswap V2 PairCreated event."""
        return signature == EVENT_SIGNATURES["PairCreated"]

    @staticmethod
    def is_pool_created_v3_event(signature: str) -> bool:
        """Check if signature matches Uniswap V3 PoolCreated event."""
        return signature == EVENT_SIGNATURES["PoolCreated"]

    @staticmethod
    def is_mint_event(signature: str) -> bool:
        """Check if signature matches Uniswap V2 Mint event."""
        return signature == EVENT_SIGNATURES["Mint"]

    @staticmethod
    def is_mint_v3_event(signature: str) -> bool:
        """Check if signature matches Uniswap V3 Mint event."""
        return signature == EVENT_SIGNATURES["MintV3"]

    @staticmethod
    def is_swap_event(signature: str) -> bool:
        """Check if signature matches Uniswap V2 Swap event."""
        return signature == EVENT_SIGNATURES["Swap"]

    @staticmethod
    def is_swap_v3_event(signature: str) -> bool:
        """Check if signature matches Uniswap V3 Swap event."""
        return signature == EVENT_SIGNATURES["SwapV3"]

    @staticmethod
    def is_burn_event(signature: str) -> bool:
        """Check if signature matches Uniswap V2 Burn event."""
        return signature == EVENT_SIGNATURES["Burn"]

    @staticmethod
    def is_sync_event(signature: str) -> bool:
        """Check if signature matches Uniswap V2 Sync event."""
        return signature == EVENT_SIGNATURES["Sync"]

    @staticmethod
    def get_event_type(signature: str) -> str:
        """
        Get human-readable event type from signature.
        
        Args:
            signature: Event signature hash
            
        Returns:
            str: Event type name or 'Unknown'
        """
        for name, sig in EVENT_SIGNATURES.items():
            if sig == signature:
                return name

        return "Unknown"
