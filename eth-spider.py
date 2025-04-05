from web3 import Web3
import websockets
import asyncio
import json
import aiohttp
import config
import abi

# Web3 instance
web3 = Web3(Web3.LegacyWebSocketProvider(config.ALCHEMY_WS_URL))

# Contract address
contract_address = Web3.to_checksum_address(config.ERC20_CONTRACT_ADDRESS)

def decode_log_data(data):
    """
    Decodes the hexadecimal data from the log into a decimal value.

    Args:
        data (str): The hexadecimal data string to decode.

    Returns:
        int: The decimal value.
    """
    return int(data, 16)

def fetch_transaction_details(tx_hash):
    """
    Fetches the details of a specific transaction.

    Args:
        tx_hash (str): The transaction hash.

    Returns:
        dict: The transaction details.
    """
    return web3.eth.get_transaction(tx_hash)

def fetch_block_details(block_number):
    """
    Fetches the details of a specific block.

    Args:
        block_number (int): The block number to fetch details for.

    Returns:
        dict: The block details.
    """
    return web3.eth.get_block(block_number)

async def send_to_telegram(message):
    """
    Sends the provided message to a Telegram chat via a bot.
    
    Args:
        message (str): The message to send.
    """
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(config.TELEGRAM_SEND_ENDPOINT, data=payload) as resp:
                if resp.status != 200:
                    print(f"Telegram error: Status {resp.status}")
                else:
                    print("Message sent to Telegram")
        except Exception as e:
            print(f"Error sending to Telegram: {e}")

async def log_transaction(log, contract):
    """
    Processes and logs the details of a transaction from the contract's event log.

    Args:
        log (dict): The log object containing the transaction data.
        contract (Web3.eth.Contract): The contract instance for the ERC-20 token.
    """
    try:
        tx_hash = log.get("transactionHash")
        block_number_hex = log.get("blockNumber")
        if not tx_hash or not block_number_hex:
            raise ValueError("Missing transactionHash or blockNumber in log.")

        try:
            block_number = int(block_number_hex, 16)
        except ValueError:
            raise ValueError(f"Invalid block number format: {block_number_hex}")

        topics = log.get("topics", [])
        from_address = "0x0"
        to_address = "0x0"

        if len(topics) > 1:
            try:
                from_address = Web3.to_checksum_address("0x" + topics[1][-40:])
            except Exception:
                pass

        if len(topics) > 2:
            try:
                to_address = Web3.to_checksum_address("0x" + topics[2][-40:])
            except Exception:
                pass

        value_in_wei = 0
        try:
            value_in_wei = decode_log_data(log.get("data", "0x0"))
        except Exception:
            pass

        tx = await asyncio.to_thread(fetch_transaction_details, tx_hash)
        block = await asyncio.to_thread(fetch_block_details, block_number)

        # Fallback values if calls fail
        decimals = await asyncio.to_thread(lambda: contract.functions.decimals().call())
        token_name = await asyncio.to_thread(lambda: contract.functions.name().call())
        token_symbol = await asyncio.to_thread(lambda: contract.functions.symbol().call())

        token_value = value_in_wei / (10 ** decimals if decimals is not None else 18)

        message = (
            f"*🕷️ New {token_name or 'ERC20'} transaction*\n\n"
            f"*Token Symbol:* `${token_symbol or 'UNKNOWN'}`\n\n"
            f"*Tx Hash:* [{tx_hash}](https://etherscan.io/tx/{tx_hash})\n"
            f"*Block:* `{block_number}` | *Block Hash:* `{block.get('hash', b'').hex() if block.get('hash') else 'N/A'}`\n\n"
            f"*From:* [{from_address}](https://etherscan.io/address/{from_address})\n"
            f"*To:* [{to_address}](https://etherscan.io/address/{to_address})\n\n"
            f"*Amount Transferred:* `{token_value:.6f} {token_symbol or ''}`\n\n"
            f"*Gas Used:* `{tx.get('gas', 'N/A')}` | *Gas Price:* `{tx.get('gasPrice', 0) / (10**9):.2f} Gwei`\n\n"
            f"*Timestamp:* `{block.get('timestamp', 'N/A')}`\n\n"
            f"[View on Etherscan](https://etherscan.io/tx/{tx_hash})"
        )

        await send_to_telegram(message)

    except Exception as e:
        print(f"Error while processing log: {e}")

async def notify_connection_error(error):
    """
    Sends a formatted WebSocket connection error message to Telegram.
    
    Args:
        error (Exception): The exception that triggered the reconnection.
    """
    error_code = getattr(error, "code", "N/A")

    error_message = (
        f"*WebSocket Error Detected!*\n\n"
        f"Connection to the Ethereum node was unexpectedly closed.\n"
        f"*Error code:* `{error_code}`\n"
        f"*Error:* `{str(error)}`\n\n"
        f"You can check the token activity manually here:\n"
        f"[View on Etherscan](https://etherscan.io/token/{config.ERC20_CONTRACT_ADDRESS})"
    )

    await send_to_telegram(error_message)

async def subscribe_to_contract_transactions(contract_address, contract_abi):
    """
    Subscribes to Ethereum contract logs and processes events.
    """
    while True:  # Ensures reconnection in case of failure
        try:
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)

            async with websockets.connect(
                config.ALCHEMY_WS_URL,
                ping_interval=None,
                ping_timeout=None,
            ) as websocket:
                # Subscribe to logs for the specific contract
                subscribe_payload = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["logs", {"address": contract_address}]
                }
                await websocket.send(json.dumps(subscribe_payload))
                print("Subscribed successfully.")

                # Process incoming logs
                while True:
                    response = await websocket.recv()
                    message_json = json.loads(response)

                    if "params" in message_json:
                        log = message_json["params"]["result"]
                        await log_transaction(log, contract)

        except (websockets.exceptions.ConnectionClosed, Exception) as e:
            await notify_connection_error(e)
            print("Reconnecting...")
            await asyncio.sleep(5)

# Start the WebSocket subscription process
asyncio.run(subscribe_to_contract_transactions(contract_address, abi.get_erc20_abi()))


#                                    . . . .
#                                    ,`,`,`,`,
#               . . . .               `\`\`\`\;
#               `\`\`\`\`,            ~|;!;!;\!
#                ~\;\;\;\|\          (--,!!!~`!       .
#               (--,\\\===~\         (--,|||~`!     ./
#                (--,\\\===~\         `,-,~,=,:. _,//
#                 (--,\\\==~`\        ~-=~-.---|\;/J,
#                  (--,\\\((```==.    ~'`~/       a |
#                    (-,.\\('('(`\\.  ~'=~|     \_.  \
#                       (,--(,(,(,'\\. ~'=|       \\_;>
#                         (,-( ,(,(,;\\ ~=/        \
#                         (,-/ (.(.(,;\\,/          )
#                          (,--/,;,;,;,\\         ./------.
#                            (==,-;-'`;'         /_,----`. \
#                    ,.--_,__.-'                    `--.  ` \
#                   (='~-_,--/        ,       ,!,___--. \  \_)
#                  (-/~(     |         \   ,_-         | ) /_|
#                  (~/((\    )\._,      |-'         _,/ /
#                   \\))))  /   ./~.    |           \_\;
#                ,__/////  /   /    )  /
#                 '===~'   |  |    (, <.
#                          / /       \. \
#                        _/ /          \_\
#                       /_!/            >_\
