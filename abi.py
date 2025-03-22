def get_erc20_abi():
    """
    Returns the standard ABI (Application Binary Interface) definition for an
    ERC-20 contract and includes an event to track the first addition of liquidity.

    An ABI specifies the functions and events exposed by a smart contract on
    the Ethereum blockchain, allowing applications to interact with it.

    Returns:
        list: A list of dictionaries defining the functions and events
        of the ERC-20 contract and Uniswap liquidity event.

    Functions included in the ABI:
        - `balanceOf(address)`: Returns the token balance of a specific address.
        - `name()`: Returns the name of the ERC-20 token.
        - `symbol()`: Returns the symbol of the ERC-20 token.
        - `decimals()`: Returns the number of decimal places used by the token.

    Events included in the ABI:
        - `Transfer(from, to, value)`: Event emitted when tokens are
          transferred from one address to another.
        - `Mint(sender, amount0, amount1)`: Event emitted when liquidity
          is first added to a Uniswap liquidity pool.
    """
    return [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}
            ],
            "name": "Transfer",
            "type": "event"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "payable": False,
            "stateMutability": "view",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "sender", "type": "address"},
                {"indexed": False, "name": "amount0", "type": "uint256"},
                {"indexed": False, "name": "amount1", "type": "uint256"}
            ],
            "name": "Mint",
            "type": "event"
        }
    ]
