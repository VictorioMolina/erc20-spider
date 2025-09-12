"""
Telegram notification system for ERC-20 Spider Bot.
Provides comprehensive notifications for all blockchain events.
"""

import asyncio
import aiohttp
import random
from typing import Optional, Dict

from .logger import Logger
from utils.humanize_number import humanize_number
from utils.map_holder_emoji import map_holder_emoji
from utils.config import (
    MIN_TOKENS_THRESHOLD,
    TELEGRAM_TIMEOUT,
    TELEGRAM_RETRY_DELAY,
    TELEGRAM_MAX_RETRIES,
    TROLL_GIFS,
)

logger = Logger().get_logger()


# todo - Check

class TelegramBot:
    """
    Telegram notification system with retry logic and formatting.
    Handles all bot communications with elegant message formatting.
    """

    def __init__(self, bot_token: str, chat_id: str):
        """
        Initialise Telegram bot with credentials.
        
        Args:
            bot_token: Telegram bot API token
            chat_id: Target chat/channel ID for notifications
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.send_endpoint = f"https://api.telegram.org/bot{bot_token}/sendAnimation"

    async def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
        timeout: int = TELEGRAM_TIMEOUT
    ) -> bool:
        """
        Send animation (GIF) with message as caption to Telegram with retry
        logic and error handling.
        
        Args:
            message: Message text to send
            parse_mode: Telegram parse mode (Markdown/HTML)
            timeout: Request timeout in seconds
            
        Returns:
            bool: True if message sent successfully
        """
        gif_url = random.choice(TROLL_GIFS)

        payload = {
            "chat_id": self.chat_id,
            "animation": gif_url,
            "caption": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        for attempt in range(TELEGRAM_MAX_RETRIES):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.send_endpoint,
                        data=payload,
                        timeout=aiohttp.ClientTimeout(total=timeout)
                    ) as response:
                        
                        if response.status == 200:
                            logger.debug("Telegram message sent successfully")
                            return True
                            
                        # Handle rate limiting
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', 60))
                            logger.warning(f"Rate limited, waiting {retry_after}s")
                            await asyncio.sleep(retry_after)
                            continue
                            
                        logger.error(f"Telegram API error: {response.status}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Telegram timeout (attempt {attempt + 1})")
                
            except Exception as error:
                logger.error(f"Telegram error (attempt {attempt + 1}): {error}")
            
            # Wait before retry unless it's the last attempt
            if attempt < TELEGRAM_MAX_RETRIES - 1:
                await asyncio.sleep(TELEGRAM_RETRY_DELAY)
        
        logger.error("Failed to send Telegram message after all retries")
        return False

    async def send_startup_notification(self, contract_address: str) -> None:
        """
        Send system startup notification with configuration details.
        
        Args:
            contract_address: ERC-20 contract being monitored
        """
        message = f"""
🚀 *ERC-20 Spider Bot Activated*

📊 *Contract Monitored*: `{contract_address}`

🎯 *Tracking Features*:
• Pool creation (V2/V3)
• Liquidity additions
• Token transfers
• DEX swaps
• CEX deposits/withdrawals
• Whale movements
• Token burns

⚡ *Alert Threshold*: {humanize_number(MIN_TOKENS_THRESHOLD)} tokens
🔍 *Status*: Actively monitoring blockchain...

*Ready to detect smart money movements!*
""".strip()

        await self.send_message(message)

    async def send_transfer_notification(
        self,
        tx_type: str,
        description: str,
        token_amount: float,
        from_addr: str,
        to_addr: str,
        tx_hash: str,
        related_pool: Optional[Dict] = None
    ) -> None:
        """
        Send comprehensive transfer event notification.
        
        Args:
            tx_type: Type of transaction with emoji
            description: Human-readable transaction description
            token_amount: Amount of tokens transferred
            from_addr: Source address
            to_addr: Destination address
            tx_hash: Transaction hash
            related_pool: Pool information if transfer is pool-related
        """
        human_amount = humanize_number(token_amount)
        holder_emoji = map_holder_emoji(token_amount)
        
        # Build context information
        context_info = ""
        if related_pool and related_pool.get("has_liquidity"):
            context_info = f"\n🏊 *Pool Context*: Active trading pool"
        elif related_pool:
            context_info = f"\n🏖️ *Pool Context*: Pre-liquidity setup"
        
        message = f"""
{holder_emoji} *{tx_type}*

💰 *Amount*: `{human_amount} tokens`
📝 *Type*: {description}

👤 *From*: `{from_addr[:8]}...{from_addr[-6:]}`
👤 *To*: `{to_addr[:8]}...{to_addr[-6:]}`{context_info}

🔗 *Transaction*: `{tx_hash[:8]}...{tx_hash[-6:]}`
[View on Etherscan](https://etherscan.io/tx/{tx_hash})
""".strip()

        await self.send_message(message)

    async def send_swap_notification(
        self,
        pool_address: str,
        token_amount: float,
        sender: str,
        recipient: str,
        tx_hash: str,
        is_first_swap: bool = False
    ) -> None:
        """
        Send swap event notification with trade context.
        
        Args:
            pool_address: Pool where swap occurred
            token_amount: Amount of tokens swapped
            sender: Swap initiator address
            recipient: Swap recipient address
            tx_hash: Transaction hash
            is_first_swap: Whether this is the first swap in this pool
        """
        human_amount = humanize_number(token_amount)
        holder_emoji = map_holder_emoji(token_amount)
        
        # Special notification for first swap
        first_swap_text = ""
        if is_first_swap:
            first_swap_text = "\n🎉 *FIRST TRADE IN POOL!*"
        
        message = f"""
{holder_emoji} *Swap Detected*

🏊 *Pool*: `{pool_address[:8]}...{pool_address[-6:]}`
💰 *Amount*: `{human_amount} tokens`{first_swap_text}

👤 *Trader*: `{sender[:8]}...{sender[-6:]}`
👤 *Recipient*: `{recipient[:8]}...{recipient[-6:]}`

🔗 *Transaction*: `{tx_hash[:8]}...{tx_hash[-6:]}`
[View Trade](https://etherscan.io/tx/{tx_hash})
[View Pool](https://etherscan.io/address/{pool_address})
""".strip()

        await self.send_message(message)

    async def send_pool_created_notification(
        self,
        pair_address: str,
        tx_hash: str,
    ) -> None:
        """
        Send new pool creation notification.
        
        Args:
            pair_address: Address of newly created pool
            tx_hash: Pool creation transaction hash
        """
        message = f"""
🆕 *New Pool Created!*

🏊 *Pool Address*: `{pair_address}`

⚠️ *Status*: Pool created, awaiting liquidity
⏳ *Next Step*: Monitoring for first liquidity addition

💡 *Note*: Trading not yet possible until liquidity is added

🔗 *Creation TX*: `{tx_hash[:8]}...{tx_hash[-6:]}`
[View Pool](https://etherscan.io/address/{pair_address})
[View Transaction](https://etherscan.io/tx/{tx_hash})
""".strip()

        await self.send_message(message)

    async def send_liquidity_added_notification(
        self,
        status_emoji: str,
        status_text: str,
        pool_address: str,
        token_amount: float,
        other_amount: float,
        tradeable_text: str,
        tx_hash: str
    ) -> None:
        """
        Send liquidity addition notification with trading assessment.
        
        Args:
            status_emoji: Emoji indicating liquidity quality
            status_text: Liquidity quality description
            pool_address: Pool receiving liquidity
            token_amount: Amount of monitored token added
            other_amount: Amount of paired token added
            tradeable_text: Trading viability assessment
            tx_hash: Liquidity addition transaction hash
        """
        token_human = humanize_number(token_amount)
        other_human = humanize_number(other_amount)
        
        message = f"""
💧 *Liquidity Added!*

{status_emoji} *Quality*: {status_text}
🏊 *Pool*: `{pool_address[:8]}...{pool_address[-6:]}`

💰 *Liquidity Amounts*:
• Monitored Token: `{token_human}`
• Paired Token: `{other_human}`

{tradeable_text}

🔗 *Transaction*: `{tx_hash[:8]}...{tx_hash[-6:]}`
[View Liquidity](https://etherscan.io/tx/{tx_hash})
[View Pool](https://etherscan.io/address/{pool_address})
""".strip()

        await self.send_message(message)

    async def send_burn_notification(
        self,
        pool_address: str,
        token_amount: float,
        other_amount: float,
        tx_hash: str
    ) -> None:
        """
        Send liquidity removal (burn) notification.
        
        Args:
            pool_address: Pool where liquidity was removed
            token_amount: Amount of monitored token removed
            other_amount: Amount of paired token removed
            tx_hash: Burn transaction hash
        """
        token_human = humanize_number(token_amount)
        other_human = humanize_number(other_amount)

        message = f"""
🔥 *Liquidity Removed!*

🏊 *Pool*: `{pool_address[:8]}...{pool_address[-6:]}`

💰 *Amounts Removed*:
• Monitored Token: `{token_human}`
• Paired Token: `{other_human}`

⚠️ *Impact*: Liquidity decreased, potential price impact

🔗 *Transaction*: `{tx_hash[:8]}...{tx_hash[-6:]}`
[View Removal](https://etherscan.io/tx/{tx_hash})
[View Pool](https://etherscan.io/address/{pool_address})
""".strip()

        await self.send_message(message)

    async def send_token_burn_notification(
        self,
        amount: float,
        from_addr: str,
        tx_hash: str
    ) -> None:
        """
        Send token burn notification.
        
        Args:
            amount: Amount of tokens burned
            from_addr: Address that burned tokens
            tx_hash: Burn transaction hash
        """
        human_amount = humanize_number(amount)
        holder_emoji = map_holder_emoji(amount)
        
        message = f"""
🔥 *Token Burn Detected!*

{holder_emoji} *Amount Burned*: `{human_amount} tokens`
👤 *Burner*: `{from_addr[:8]}...{from_addr[-6:]}`

📊 *Effect*: Token supply decreased (deflationary)

🔗 *Transaction*: `{tx_hash[:8]}...{tx_hash[-6:]}`
[View Burn](https://etherscan.io/tx/{tx_hash})
""".strip()

        await self.send_message(message)

    async def send_error_notification(self, error_type: str, details: str) -> None:
        """
        Send system error notifications for monitoring.
        
        Args:
            error_type: Type/category of error
            details: Error details and context
        """
        message = f"""
🚨 *System Alert*

*Error Type*: {error_type}
*Details*: {details}

*Timestamp*: `{asyncio.get_event_loop().time()}`
*Status*: Attempting automatic recovery...
""".strip()

        await self.send_message(message)

    async def send_system_status(
        self,
        events_processed: int,
        uptime_hours: float,
        events_per_hour: float
    ) -> None:
        """
        Send periodic system status updates.
        
        Args:
            events_processed: Total events processed
            uptime_hours: System uptime in hours
            events_per_hour: Processing rate
        """
        message = f"""
📊 *System Status Report*

⚡ *Events Processed*: {events_processed:,}
⏱️ *Uptime*: {uptime_hours:.1f} hours
📈 *Processing Rate*: {events_per_hour:.1f} events/hour

✅ *Status*: Operational
🔍 *Monitoring*: Active
""".strip()

        await self.send_message(message)
