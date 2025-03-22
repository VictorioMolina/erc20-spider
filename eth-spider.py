from web3 import Web3
import websockets
import asyncio
import json
import requests
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

def send_to_telegram(message):
    """
    Sends the provided message to a Telegram chat via a bot.
    
    Args:
        message (str): The message to send.
    """
    payload = {
        "chat_id": config.TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"  # Enables Markdown formatting
    }

    try:
        response = requests.post(config.TELEGRAM_SEND_ENDPOINT, data=payload)

        if response.status_code != 200:
            print(f"Failed to send message to Telegram. Status Code: {response.status_code}")
        else:
            print("Message sent to Telegram successfully.")

    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Telegram: {e}")

def log_transaction(log, contract):
    """
    Processes and logs the details of a transaction from the contract's event log.

    Args:
        log (dict): The log object containing the transaction data.
        contract (Web3.eth.Contract): The contract instance for the ERC-20 token.
    """
    tx_hash = log["transactionHash"]
    block_number = int(log["blockNumber"], 16)

    # Decode the 'from' and 'to' addresses
    from_address = Web3.to_checksum_address(log["topics"][1][26:] if len(log["topics"]) > 1 else "Unknown")
    to_address = Web3.to_checksum_address(log["topics"][2][26:] if len(log["topics"]) > 2 else "Unknown")

    # Decode the value transferred
    value_in_wei = decode_log_data(log["data"])

    # Fetch additional transaction and block details
    tx = fetch_transaction_details(tx_hash)
    block = fetch_block_details(block_number)

    # Convert value to tokens using the contract's decimals
    decimals = contract.functions.decimals().call()
    token_value = value_in_wei / (10 ** decimals)

    # Get the token symbol and name
    token_name = contract.functions.name().call()
    token_symbol = contract.functions.symbol().call()

    # Formatted output
    message = (
        f"*🕷️ New {token_name} transaction*\n\n"
        f"*Token Symbol:* `${token_symbol}`\n\n"
        f"*Tx Hash:* [{tx_hash}](https://etherscan.io/tx/{tx_hash})\n"
        f"*Block:* `{block_number}` | *Block Hash:* `{block['hash'].hex()}`\n\n"
        f"*From:* [{from_address}](https://etherscan.io/address/{from_address})\n"
        f"*To:* [{to_address}](https://etherscan.io/address/{to_address})\n\n"
        f"*Amount Transferred:* `{token_value:.6f} {token_symbol}`\n\n"
        f"*Gas Used:* `{tx['gas']}` | *Gas Price:* `{tx['gasPrice'] / (10**9)} Gwei`\n\n"
        f"*Timestamp:* `{block['timestamp']}`\n\n"
        f"[View on Etherscan](https://etherscan.io/tx/{tx_hash})"
    )

    print(message)

    # Send to Telegram
    send_to_telegram(message)

async def subscribe_to_contract_transactions(contract_address, contract_abi):
    """
    Subscribes to Ethereum contract logs and processes events.
    """
    while True:  # Ensures reconnection in case of failure
        try:
            contract = web3.eth.contract(address=contract_address, abi=contract_abi)

            async with websockets.connect(config.ALCHEMY_WS_URL) as websocket:
                # Subscribe to logs for the specific contract
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": ["logs", {"address": contract_address}]
                }
                await websocket.send(json.dumps(request))
                print("Subscribed successfully.")

                # Process incoming logs
                while True:
                    message = await websocket.recv()
                    message_json = json.loads(message)

                    if "params" in message_json:
                        log = message_json["params"]["result"]
                        log_transaction(log, contract)

        except (websockets.exceptions.ConnectionClosed, Exception) as e:
            print(f"Error: {e}. Reconnecting...")
            send_to_telegram("⚡️🚨 *SYSTEM ERROR* - Analysis interrupted. Retrying... 💻💥")
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
