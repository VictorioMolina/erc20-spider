"""
ERC-20 Spider Bot with comprehensive event monitoring.
Tracks transfers, swaps, pool creation, liquidity additions, burns and mints.
"""

import asyncio
import json
import time
from typing import List
from websockets import connect

from .logger import Logger
from .telegram_bot import TelegramBot
from .event_decoder import EventDecoder, EventSignatureValidator
from .pool_tracker import PoolTracker
from .transaction_classifier import TransactionClassifier
from utils.config import (
    ALCHEMY_WS_URL,
    ERC20_CONTRACT_ADDRESS,
    CONTRACT_DECIMALS,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    WS_PING_INTERVAL,
    WS_PING_TIMEOUT,
    WS_RECONNECT_DELAY,
    MIN_TOKENS_THRESHOLD,
    UNISWAP_V2_FACTORY,
    UNISWAP_V3_FACTORY,
    DEX_ROUTERS,
    ZERO_ADDRESS,
    BURN_ADDRESS,
)

logger = Logger().get_logger()


# todo - Check

class SpiderBot:
    """
    Main bot class orchestrating blockchain event monitoring and notifications.
    Handles WebSocket connections, event processing, and system lifecycle.
    """

    def __init__(self):
        """Initialise bot components and tracking state."""
        self.contract_address = ERC20_CONTRACT_ADDRESS.lower()
        self.telegram = TelegramBot(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.pool_tracker = PoolTracker()
        self.classifier = TransactionClassifier(self.contract_address)

        # System state tracking
        self.websocket = None
        self.sub_id = 1
        self.should_stop = asyncio.Event()
        self.events_processed = 0
        self.start_time = time.time()

        # Performance monitoring
        self._last_performance_log = time.time()
        self._performance_log_interval = 300  # 5 minutes

    async def start(self) -> None:
        """
        Start the spider bot monitoring system.
        Initialises logging and begins WebSocket subscription loop.
        """
        Logger().log_system_info()
        
        # Load existing pools before starting
        await self._load_existing_pools()
        
        # Send startup notification
        await self.telegram.send_startup_notification(ERC20_CONTRACT_ADDRESS)
        logger.info(f"Monitoring contract: {ERC20_CONTRACT_ADDRESS}")
        
        # Begin monitoring loop
        await self._subscription_loop()

    async def stop(self) -> None:
        """Gracefully shutdown the bot system."""
        logger.info("Shutdown signal received, stopping spider bot...")
        self.should_stop.set()
        
        # Log final performance metrics
        uptime = time.time() - self.start_time
        Logger().log_performance_metrics(self.events_processed, uptime)

    async def _load_existing_pools(self):
        """Load existing pools that contain our token"""
        try:
            # This would typically call an API to find existing pools
            # For now, we'll start with an empty list and discover pools dynamically
            logger.info("Pool discovery will happen dynamically through factory events")
            
        except Exception as e:
            logger.error(f"Error loading existing pools: {e}")

    async def _subscription_loop(self) -> None:
        """
        Main subscription loop with automatic reconnection.
        Maintains persistent WebSocket connection to Alchemy.
        """
        while not self.should_stop.is_set():
            try:
                async with connect(
                    ALCHEMY_WS_URL,
                    ping_interval=WS_PING_INTERVAL,
                    ping_timeout=WS_PING_TIMEOUT
                ) as websocket:
                    self.websocket = websocket
                    logger.info("WebSocket connected successfully")
                    
                    await self._setup_subscriptions(websocket)
                    await self._process_messages(websocket)
                    
            except Exception as error:
                logger.error(f"WebSocket connection error: {error}")
                
                if not self.should_stop.is_set():
                    logger.info(f"Reconnecting in {WS_RECONNECT_DELAY} seconds...")
                    await asyncio.sleep(WS_RECONNECT_DELAY)

    async def _setup_subscriptions(self, websocket) -> None:
        """
        Configure WebSocket subscriptions for event monitoring.
        Subscribes to factories, token contract, and known pools.
        """
        # Subscribe to factories and token contract
        fixed_addresses = [
            ERC20_CONTRACT_ADDRESS,
            UNISWAP_V2_FACTORY,
            UNISWAP_V3_FACTORY,
        ]
        await self._subscribe_to_addresses(websocket, fixed_addresses)
        
        # Subscribe to existing pools
        pool_addresses = [
            pool["address"] for pool in self.pool_tracker.pools.values()
        ]
        if pool_addresses:
            await self._subscribe_to_addresses(websocket, pool_addresses)
        
        logger.info(f"Subscriptions configured: {len(fixed_addresses)} fixed addresses, {len(pool_addresses)} pools")

    async def _subscribe_to_addresses(
        self,
        websocket,
        addresses: List[str]
    ) -> None:
        """
        Subscribe to logs for specified addresses.
        
        Args:
            websocket: Active WebSocket connection
            addresses: List of addresses to subscribe to
        """
        if not addresses:
            return
        
        subscription = {
            "jsonrpc": "2.0",
            "id": self.sub_id,
            "method": "eth_subscribe",
            "params": ["logs", {"address": [addr.lower() for addr in addresses]}]
        }
        self.sub_id += 1
        
        await websocket.send(json.dumps(subscription))
        logger.debug(f"Subscribed to: {', '.join(addresses)}")

    async def _process_messages(self, websocket) -> None:
        """
        Process incoming WebSocket messages and route events appropriately.
        Handles subscription confirmations and blockchain event notifications.
        """
        async for message in websocket:
            if self.should_stop.is_set():
                break
                
            try:
                data = json.loads(message)
                if "params" in data and "result" in data["params"]:
                    await self._handle_event(data["params"]["result"])
                
            except json.JSONDecodeError:
                logger.warning("Received invalid JSON message")
            except Exception as error:
                logger.error(f"Message processing error: {error}")

    async def _handle_event(self, log: dict) -> None:
        """
        Route blockchain events to appropriate handlers based on signature.
        
        Args:
            log: Parsed event log data
        """
        topics = log.get("topics", [])
        if not topics:
            return
            
        # Increment event counter and check performance logging
        self.events_processed += 1
        await self._maybe_log_performance()
        
        # Route based on event signature
        signature = topics[0]

        if EventSignatureValidator.is_transfer_event(signature):
            await self._handle_transfer(log)
            
        elif EventSignatureValidator.is_pair_created_event(signature):
            await self._handle_pair_created(log)
            
        elif EventSignatureValidator.is_pool_created_v3_event(signature):
            await self._handle_pool_created_v3(log)
            
        elif EventSignatureValidator.is_mint_event(signature):
            await self._handle_mint_v2(log)
            
        elif EventSignatureValidator.is_mint_v3_event(signature):
            await self._handle_mint_v3(log)
            
        elif EventSignatureValidator.is_swap_event(signature):
            await self._handle_swap_v2(log)
            
        elif EventSignatureValidator.is_swap_v3_event(signature):
            await self._handle_swap_v3(log)
            
        elif EventSignatureValidator.is_burn_event(signature):
            await self._handle_burn_v2(log)
            
        elif EventSignatureValidator.is_sync_event(signature):
            await self._handle_sync_v2(log)

    async def _handle_transfer(self, log: dict) -> None:
        """
        Process ERC-20 transfer events and classify transaction types.
        
        Args:
            log: Raw transfer event log data
        """
        if log["address"].lower() != self.contract_address:
            return
            
        decoded = EventDecoder.decode_transfer(log)
        if not decoded:
            return
            
        from_addr, to_addr, amount = decoded

        if amount < MIN_TOKENS_THRESHOLD:
            return

        # Check for token burns (transfer to zero address or burn address)
        if to_addr.lower() in [ZERO_ADDRESS.lower(), BURN_ADDRESS.lower()]:
            logger.info(f"Token burn detected: {amount:.2f} tokens")
            await self.telegram.send_token_burn_notification(
                amount=amount,
                from_addr=from_addr,
                tx_hash=log["transactionHash"]
            )
            return

        # Check if transfer is to a DEX router (potential swap)
        if to_addr.lower() in [router.lower() for router in DEX_ROUTERS]:
            logger.info(f"Potential swap detected: {amount:.2f} tokens to DEX router")
            await self._investigate_potential_swap(log["transactionHash"], from_addr, amount)
            return

        related_pool = self.classifier.find_related_pool(
            from_addr, to_addr, self.pool_tracker
        )
        
        tx_type, description = self.classifier.classify_transaction_type(
            from_addr, to_addr, related_pool
        )
        
        logger.info(f"Transfer: {amount:.2f} tokens - {tx_type}")
        
        await self.telegram.send_transfer_notification(
            tx_type=tx_type,
            description=description,
            token_amount=amount,
            from_addr=from_addr,
            to_addr=to_addr,
            tx_hash=log["transactionHash"],
            related_pool=related_pool
        )

    async def _investigate_potential_swap(self, tx_hash: str, from_addr: str, amount: float):
        """
        Investigate a potential swap transaction.
        
        Args:
            tx_hash: Transaction hash to investigate
            from_addr: Address that initiated the swap
            amount: Amount of tokens involved
        """
        # This would typically involve querying the transaction details
        # to confirm it's actually a swap and get more details
        logger.info(f"Investigating potential swap: {tx_hash}")

        # For now, just send a basic notification
        await self.telegram.send_swap_notification(
            pool_address="DEX Router",
            token_amount=amount,
            sender=from_addr,
            recipient="Unknown",
            tx_hash=tx_hash,
            is_first_swap=False
        )

    async def _handle_pair_created(self, log: dict) -> None:
        """
        Process Uniswap V2 pair creation events.
        
        Args:
            log: Raw pair creation event log data
        """
        decoded = EventDecoder.decode_pair_created(log)
        if not decoded:
            return
            
        token0, token1, pair = decoded
        
        # Check if our token is in the pair
        if not self.classifier.is_contract_involved(token0, token1):
            return
            
        self.pool_tracker.add_pool(pair, token0, token1, "V2")
        
        # Subscribe to the new pool for swap events
        if self.websocket:
            await self._subscribe_to_addresses(self.websocket, [pair])
        
        logger.info(f"New V2 pair with our token: {pair}")
        
        await self.telegram.send_pool_created_notification(
            pair_address=pair,
            tx_hash=log["transactionHash"]
        )

    async def _handle_pool_created_v3(self, log: dict) -> None:
        """
        Process Uniswap V3 pool creation events.
        
        Args:
            log: Raw V3 pool creation event log data
        """
        decoded = EventDecoder.decode_pool_created_v3(log)
        if not decoded:
            return
            
        token0, token1, pool, fee = decoded
        
        # Check if our token is in the pool
        if not self.classifier.is_contract_involved(token0, token1):
            return
            
        self.pool_tracker.add_pool(pool, token0, token1, "V3")
        
        # Subscribe to the new pool for swap events
        if self.websocket:
            await self._subscribe_to_addresses(self.websocket, [pool])
        
        logger.info(f"New V3 pool with our token: {pool} (fee: {fee/10000}%)")
        
        await self.telegram.send_pool_created_notification(
            pair_address=pool,
            tx_hash=log["transactionHash"]
        )

    async def _handle_mint_v2(self, log: dict) -> None:
        """
        Process Uniswap V2 mint events (liquidity additions).
        
        Args:
            log: Raw V2 mint event log data
        """
        pool_addr = log["address"].lower()
        pool_info = self.pool_tracker.get_pool_info(pool_addr)
        if not pool_info:
            return
            
        decoded = EventDecoder.decode_mint_event(log)
        if not decoded:
            return
            
        amount0, amount1 = decoded
        token_amount = amount0 if pool_info["token0"].lower() == self.contract_address else amount1
        other_amount = amount1 if pool_info["token0"].lower() == self.contract_address else amount0
        
        if token_amount < MIN_TOKENS_THRESHOLD:
            return

        tx_hash = log["transactionHash"]
        self.pool_tracker.mark_liquidity_added(pool_addr, tx_hash, amount0, amount1)
        
        emoji, text, tradeable = self.classifier.assess_liquidity_quality(token_amount)
        
        logger.info(f"V2 liquidity added: {token_amount:.2f} tokens to {pool_addr}")

        await self.telegram.send_liquidity_added_notification(
            status_emoji=emoji,
            status_text=text,
            pool_address=pool_addr,
            token_amount=token_amount,
            other_amount=other_amount,
            tradeable_text=tradeable,
            tx_hash=tx_hash
        )

    async def _handle_mint_v3(self, log: dict) -> None:
        """
        Process Uniswap V3 mint events (liquidity additions).
        
        Args:
            log: Raw V3 mint event log data
        """
        pool_addr = log["address"].lower()
        pool_info = self.pool_tracker.get_pool_info(pool_addr)
        if not pool_info:
            return
            
        decoded = EventDecoder.decode_mint_v3_event(log)
        if not decoded:
            return
            
        amount0, amount1 = decoded
        token_amount = amount0 if pool_info["token0"].lower() == self.contract_address else amount1
        other_amount = amount1 if pool_info["token0"].lower() == self.contract_address else amount0
        
        if token_amount < MIN_TOKENS_THRESHOLD:
            return
            
        tx_hash = log["transactionHash"]
        self.pool_tracker.mark_liquidity_added(pool_addr, tx_hash, amount0, amount1)
        
        emoji, text, tradeable = self.classifier.assess_liquidity_quality(token_amount)
        
        logger.info(f"V3 liquidity added: {token_amount:.2f} tokens to {pool_addr}")
        
        await self.telegram.send_liquidity_added_notification(
            status_emoji=emoji,
            status_text=text,
            pool_address=pool_addr,
            token_amount=token_amount,
            other_amount=other_amount,
            tradeable_text=tradeable,
            tx_hash=tx_hash
        )

    async def _handle_burn_v2(self, log: dict) -> None:
        """
        Process Uniswap V2 burn events (liquidity removals).
        
        Args:
            log: Raw V2 burn event log data
        """
        pool_addr = log["address"].lower()
        pool_info = self.pool_tracker.get_pool_info(pool_addr)
        if not pool_info:
            return
            
        decoded = EventDecoder.decode_burn_event(log)
        if not decoded:
            return
            
        amount0, amount1 = decoded
        token_amount = amount0 if pool_info["token0"].lower() == self.contract_address else amount1
        other_amount = amount1 if pool_info["token0"].lower() == self.contract_address else amount0
        
        if token_amount < MIN_TOKENS_THRESHOLD:
            return
            
        # Extract sender from topics (first topic is the event signature, second is sender)
        topics = log.get("topics", [])
        if len(topics) < 2:
            logger.debug("Burn event missing sender topic")
            return

        tx_hash = log["transactionHash"]
        
        logger.info(f"V2 liquidity removed: {token_amount:.2f} tokens from {pool_addr}")
        
        await self.telegram.send_burn_notification(
            pool_address=pool_addr,
            token_amount=token_amount,
            other_amount=other_amount,
            tx_hash=tx_hash
        )

    async def _handle_sync_v2(self, log: dict) -> None:
        """
        Process Uniswap V2 sync events (reserve updates).
        
        Args:
            log: Raw V2 sync event log data
        """
        # Sync events indicate reserve updates but don't contain specific amounts
        # We can use these to track pool health but won't send notifications
        pool_addr = log["address"].lower()
        pool_info = self.pool_tracker.get_pool_info(pool_addr)
        
        if pool_info:
            logger.debug(f"Sync event for pool: {pool_addr}")

    async def _handle_swap_v2(self, log: dict) -> None:
        """
        Process Uniswap V2 swap events.
        
        Args:
            log: Raw V2 swap event log data
        """
        pool_addr = log["address"].lower()
        pool_info = self.pool_tracker.get_pool_info(pool_addr)
        if not pool_info:
            return
            
        decoded = EventDecoder.decode_swap_v2_event(log)
        if not decoded:
            return
            
        sender, to, a0_in, a1_in, a0_out, a1_out = decoded
        if pool_info["token0"].lower() == self.contract_address:
            amount = (a0_in - a0_out) / 10 ** CONTRACT_DECIMALS
        else:
            amount = (a1_in - a1_out) / 10 ** CONTRACT_DECIMALS
        
        if abs(amount) < MIN_TOKENS_THRESHOLD:
            return
        
        is_first = self.pool_tracker.mark_first_swap(pool_addr, log["transactionHash"])
        
        logger.info(f"V2 swap: {amount:.2f} tokens in {pool_addr}")
        
        await self.telegram.send_swap_notification(
            pool_address=pool_addr,
            token_amount=abs(amount),
            sender=sender,
            recipient=to,
            tx_hash=log["transactionHash"],
            is_first_swap=is_first
        )

    async def _handle_swap_v3(self, log: dict) -> None:
        """
        Process Uniswap V3 swap events.
        
        Args:
            log: Raw V3 swap event log data
        """
        pool_addr = log["address"].lower()
        pool_info = self.pool_tracker.get_pool_info(pool_addr)
        if not pool_info:
            return
            
        decoded = EventDecoder.decode_swap_v3_event(log)
        if not decoded:
            return
            
        sender, recipient, amount0, amount1, _, _ = decoded
        if pool_info["token0"].lower() == self.contract_address:
            amount = amount0 / 10 ** CONTRACT_DECIMALS
        else:
            amount = amount1 / 10 ** CONTRACT_DECIMALS
        
        if abs(amount) < MIN_TOKENS_THRESHOLD:
            return
        
        is_first = self.pool_tracker.mark_first_swap(pool_addr, log["transactionHash"])
        
        logger.info(f"V3 swap: {amount:.2f} tokens in {pool_addr}")
        
        await self.telegram.send_swap_notification(
            pool_address=pool_addr,
            token_amount=abs(amount),
            sender=sender,
            recipient=recipient,
            tx_hash=log["transactionHash"],
            is_first_swap=is_first
        )

    async def _maybe_log_performance(self) -> None:
        """Log performance metrics at regular intervals."""
        now = time.time()
        if now - self._last_performance_log >= self._performance_log_interval:
            uptime = now - self.start_time
            Logger().log_performance_metrics(self.events_processed, uptime)
            self._last_performance_log = now
