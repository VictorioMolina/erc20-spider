"""
Configuration module for ERC-20 Spider Bot.
Contains all system constants and network settings.
"""

# Alchemy setup
ALCHEMY_API_KEY = "ALCHEMY_API_KEY"
ALCHEMY_WS_URL = f"wss://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

# Telegram bot credentials
TELEGRAM_BOT_TOKEN = "TELEGRAM_BOT_TOKEN"
TELEGRAM_CHAT_ID = "TELEGRAM_CHAT_ID"

# ERC-20 contract address to monitor
ERC20_CONTRACT_ADDRESS = "0xdA5e1988097297dCdc1f90D4dFE7909e847CBeF6"
CONTRACT_DECIMALS = 18

# Notification thresholds
MIN_TOKENS_THRESHOLD = 7_500_000   # Minimum tokens for notification
MIN_LIQUIDITY_THRESHOLD = 100_000  # Minimum for substantial liquidity

# Blockchain event signatures
EVENT_SIGNATURES = {
    # ERC-20 Standard Events
    "Transfer": "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",

    # Uniswap V2 Events
    "PairCreated": "0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9",
    "Mint": "0x4c209b5fc8ad50758f13e2e1088ba56a560dff690a1c6fef26394f4c03821c4f",
    "Swap": "0xd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822",
    "Burn": "0xdccd412f0b1252819cb1fd330b93224ca42612892bb3f4f789976e6d81936496",
    "Sync": "0x1c411e9a96e071241c2f21f7726b17ae89e3cab4c78be50e062b03a9fffbbad1",
    
    # Uniswap V3 Events
    "PoolCreated": "0x783cca1c0412dd0d695e784568c96da2e9c22ff989357a2e8b1d9b2b4e6b7118",
    "MintV3": "0x7a53080ba414158be7ec69b987b5fb7d07dee101fe85488f0853ae16239d0bde",
    "SwapV3": "0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67",
}

# Uniswap factory addresses
UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
UNISWAP_V3_FACTORY = "0x1F98431c8aD98523631AE4a59f267346ea31F984"

# Special addresses
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
BURN_ADDRESS = "0x000000000000000000000000000000000000dEaD"

# Decentralised exchange routers
DEX_ROUTERS = {
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",  # Uniswap V2 Router
    "0xe592427a0aece92de3edee1f18e0157c05861564",  # Uniswap V3 Router
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f",  # SushiSwap Router
    "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506",  # SushiSwap V2 Router
    "0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45",  # Uniswap V3 SwapRouter02
    "0x1111111254fb6c44bac0bed2854e76f90643097d",  # 1inch V4 Router
}

# Centralised exchange addresses
CEX_ADDRESSES = {
    # Binance
    "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",  # Binance 7
    "0xd551234ae421e3bcba99a0da6d736074f22192ff",  # Binance 8
    "0x564286362092d8e7936f0549571a803b203aaced",  # Binance 9
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d",  # Binance 14
    
    # Coinbase
    "0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43",  # Coinbase 1
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3",  # Coinbase 2
    "0x503828976d22510aad0201ac7ec88293211d23da",  # Coinbase 3
    
    # Other Major Exchanges
    "0x77696bb39917c91a0c3908d577d5e322095425ca",  # OKEx
    "0x2910543af39aba0cd09dbb2d50200b3e800a63d2",  # Kraken 7
    "0x0a869d79a7052c7f1b55a8ebabbea3420f0d1e13",  # Bitfinex
    "0x6cc5f688a315f3dc28a7781717a9a798a59fda7b",  # OKEx 2
    "0x236f9f97e0e62388479bf9e5ba4889e46b0273c3",  # Huobi 10
    "0x46340b20830761efd32832a74d7169b29feb9758",  # Crypto.com
    "0x28c6c06298d514db089934071355e5743bf21d60",  # Binance 14
}

# WebSocket settings
WS_PING_INTERVAL = 20         # WebSocket ping interval in seconds
WS_PING_TIMEOUT = 10          # WebSocket ping timeout in seconds
WS_RECONNECT_DELAY = 5        # Seconds between reconnection attempts

# Telegram settings
TELEGRAM_TIMEOUT = 10         # Telegram API timeout in seconds
TELEGRAM_RETRY_DELAY = 2      # Delay between telegram retry attempts
TELEGRAM_MAX_RETRIES = 3      # Maximum telegram retry attempts

# Logging configuration
LOG_LEVEL = "INFO"            # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Holders classification system
HOLDERS_EMOJIS = {
    0: "🦐",           # Shrimp (0-999 tokens)
    1_000: "🐠",       # Fish (1K-9,999 tokens)
    10_000: "🦀",      # Crab (10K-49,999 tokens)
    50_000: "🐬",      # Dolphin (50K-499,999 tokens)
    500_000: "🐙",     # Octopus (500K-999,999 tokens)
    1_000_000: "🦈",   # Shark (1M-1,999,999 tokens)
    2_000_000: "🐋",   # Whale (2M-9,999,999 tokens)
    10_000_000: "🦑",  # Kraken (10M+ tokens)
}

# Troll GIFs for notifications
TROLL_GIFS = [
    "https://c.tenor.com/AjBE7eX3C_MAAAAd/tenor.gif",
    "https://c.tenor.com/0upd1gTK-ncAAAAC/tenor.gif",
    "https://c.tenor.com/W7199QiId5MAAAAd/tenor.gif",
    "https://c.tenor.com/DXLfpm42cFsAAAAd/tenor.gif",
    "https://c.tenor.com/q8wuf9AnfTMAAAAC/tenor.gif",
    "https://c.tenor.com/-6TykAcNNUIAAAAC/tenor.gif"
    "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExbWt4dXgyaHpsbnd0NW5vd2J4M2xucWV6cXFxOHhkcnR6cHQ1b25mYSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/5e1TowRHUjZalmk7cc/giphy.gif",
    "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExcm9ycHNvZGRoaWpicGhvcHByZmZ6YXhvN3ZpbDE3dmluY2RxNDZ1ZCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/Ad0ZJqcK8zEfm/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExcGpoM2kxdXFtOG1idWdyeG12YXlvd3R5MGI0NGwzMG5yOGk1NDQwcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/mFPycAuErzMcRzhkOH/giphy.gif",
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExejBlYmI0anFpNnQ0c2xpZGRiNTBoM3lreTdjeGg2dmxsbDcydXc3eiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/26gsk7l9HB575rQwo/giphy.gif",
    "https://media.tenor.com/pvr5Vxcs6VoAAAAM/barron-trump-let-me-hear-it.gif",
    "https://c.tenor.com/cF8pfkDnmTIAAAAd/tenor.gif",
    "https://c.tenor.com/L9zah9-Z8cMAAAAd/tenor.gif",
    "https://c.tenor.com/wABnnf-XauUAAAAC/tenor.gif",
    "https://c.tenor.com/f1w4R2RhdUgAAAAd/tenor.gif",
    "https://c.tenor.com/_NoTiHjR_sMAAAAd/tenor.gif",
    "https://c.tenor.com/7i0vZSGzPCIAAAAC/tenor.gif",
    "https://c.tenor.com/-Z_d0-R2JOEAAAAC/tenor.gif",
    "https://c.tenor.com/bwxvhBEflgIAAAAC/tenor.gif",
]
