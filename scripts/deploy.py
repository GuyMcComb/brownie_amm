# Token 0 is DAI
# Token 1 is WETH

"""
In this script, there are two accounts: account0 and account1.

Steps:
Account0 will deploy the liquidity pool contract.

Account0 + Account1 will then deposit eth into the weth contract to recieve weth
Account0 + Account1 trades some of the weth for dai

Account0 deposits equal value of each into the LP pool

Account0 the swaps some dai and gets weth changing the reserves in the pool and therefore changing price

Account1 sees this and decides to arbitrage it and brings the pool back to equal value. This is
done by depositing weth and getting dai

Account0 proceeds to widthdraw their funds and burns their lp tokens.

"""
from brownie import LiquidityPool, network, config, accounts, interface
from scripts.helpful_scripts import get_account
from web3 import Web3
import math
from datetime import datetime
from pprint import pprint

web3 = Web3(Web3.HTTPProvider("HTTP://127.0.0.1:7545"))

uni_router_address = config["networks"]["mainnet-fork"]["uni_router_address"]
dai_address = config["networks"]["mainnet-fork"]["dai_token"]
weth_address = config["networks"]["mainnet-fork"]["weth_token"]

address_to_tickers = {dai_address: "DAI", weth_address: "WETH"}

tickers_to_address = {"DAI": dai_address, "WETH": weth_address}

one_eth = Web3.toWei(1, "ether")

half_eth = one_eth / 2
quarter_eth = one_eth / 4

lp_token_name = "ETH-DAI-LPTOKEN"
lp_token_ticker = "EDLP"


def find_lp_token(liquidity_pool):
    address = liquidity_pool.returnTokenAddress()
    return address


def deploy_liquitypool(
    token_0_address, token_1_address, token_name, token_ticker, account
):

    liquidity_pool = LiquidityPool.deploy(
        [token_0_address, token_1_address], token_name, token_ticker, {"from": account}
    )

    return liquidity_pool


def get_weth(weth_amount, account):
    """
    Mints WETH by depositing ETH.
    """
    # add your keystore ID as an argument to this call
    weth = interface.WethInterface(
        config["networks"][network.show_active()]["weth_token"]
    )
    tx = weth.deposit({"from": account, "value": weth_amount})
    print(f"Account: {account} received {weth_amount} WETH")
    return tx


def approve_token(token_address, amount, sender, account_holder):
    token = interface.IERC20(token_address)
    tx = token.approve(sender, amount, {"from": account_holder})
    print(
        f"Account: {account_holder} approved account: {sender} to move {amount} of {address_to_tickers[token_address]}."
    )
    return tx


def get_quote(qty, tokens):
    uni_router = interface.IUniswapV2Router02(uni_router_address)
    amount = uni_router.getAmountsOut(qty, [tokens[0], tokens[1]])
    print(
        f"{qty} {address_to_tickers[tokens[0]]} will get you {amount[1]} of {address_to_tickers[tokens[1]]} - Note this is in the smallest denomination"
    )
    return amount


def get_balance(token_address, account):
    token_contract = interface.IERC20(token_address)
    account_balance = token_contract.balanceOf(account)

    print(
        f"Account {account} has balance of {account_balance} for {address_to_tickers[token_address]}."
    )

    return account_balance


def swap_tokens(qty, from_token, to_token, account):
    uni_router = interface.IUniswapV2Router02(uni_router_address)
    expiryDate = math.floor(datetime.now().timestamp() + 9000000)
    tx = uni_router.swapExactTokensForTokens(
        qty, 0, [from_token, to_token], account, expiryDate, {"from": account}
    )
    return tx


def main():
    account0 = get_account(index=0)
    account1 = get_account(index=1)

    # Account 0 and Account 1 getting WETH to Swap on Uniswap for DAI
    get_weth(one_eth, account0)
    get_weth(one_eth, account1)
    get_balance(weth_address, account0)
    get_balance(weth_address, account1)

    print("Getting quote of 0.25 WETH for DAI")
    half_eth_of_dai = get_quote(half_eth, [weth_address, dai_address])[1]

    quarter_eth_of_dai = half_eth_of_dai / 2

    print("Approving_tokens")
    approve_token(weth_address, half_eth, uni_router_address, account0)
    approve_token(weth_address, half_eth, uni_router_address, account1)

    # Swapping 0.5 WETH for DAI
    print("Swapping Tokens")
    swap_tokens(half_eth, weth_address, dai_address, account0)
    swap_tokens(half_eth, weth_address, dai_address, account1)

    print("Tokens swapped on Uniswap, checking account0 and account1 balances")
    get_balance(weth_address, account0)
    get_balance(dai_address, account0)
    print("-----")
    get_balance(weth_address, account1)
    get_balance(dai_address, account1)

    #### Now deploying the liquidity pool
    # Account 0 Deploying liquidity pool
    liquidity_pool = deploy_liquitypool(
        dai_address, weth_address, lp_token_name, lp_token_ticker, account0
    )

    print(f"Liquidity Pool deployed to address: {liquidity_pool.address}")

    lp_token_address = find_lp_token(liquidity_pool)
    print(f"Liquidity Pool Token deployed to address: {lp_token_address}")

    # Adding tickers to mappings
    address_to_tickers[lp_token_address] = lp_token_ticker
    tickers_to_address[lp_token_ticker] = lp_token_address

    approve_token(dai_address, quarter_eth_of_dai, liquidity_pool.address, account0)
    approve_token(weth_address, quarter_eth, liquidity_pool.address, account0)

    print(f"Now depositing funds into liquidity pool.")
    print(f"Depositing DAI {quarter_eth_of_dai} and WETH {quarter_eth}")
    liquidity_pool.deposit(
        [dai_address, weth_address],
        [quarter_eth_of_dai, quarter_eth],
        {"from": account0},
    )

    print(
        "Tokens deposited into liquidity pool, checking account0 and liquidity pool balances"
    )
    get_balance(weth_address, account0)
    get_balance(dai_address, account0)
    get_balance(lp_token_address, account0)
    print("----------")
    get_balance(weth_address, liquidity_pool.address)
    get_balance(dai_address, liquidity_pool.address)

    print(f"Current Exchange Rate DAI/ETH: {liquidity_pool.quote()}")

    print("Account 1 is performing a swap")
    print("Approving Tokens")
    approve_token(dai_address, quarter_eth_of_dai, liquidity_pool.address, account1)
    print("Swapping Tokens")
    print(quarter_eth_of_dai, "Quarter ETH of DIA")
    print(liquidity_pool.calculatePercentage(100 - 5, quarter_eth_of_dai, 100))

    tx = liquidity_pool.swapPutIn(
        [dai_address, weth_address], quarter_eth_of_dai, {"from": account1}
    )

    print(f"Swapped {quarter_eth_of_dai} DAI for {tx.return_value} WETH")

    print(
        "Tokens swapped into liquidity pool, checking account1 and liquidity pool balances"
    )
    get_balance(weth_address, account1)
    get_balance(dai_address, account1)
    print("----------")
    get_balance(weth_address, liquidity_pool.address)
    get_balance(dai_address, liquidity_pool.address)

    print(f"Current Exchange Rate DAI/ETH: {liquidity_pool.quote()}")

    # Now account0 will take advantage of this arbitrage and rebalance the pool.
    # Calculating how much is out of the scope of this script we will use tx.return_value

    approve_token(weth_address, tx.return_value, liquidity_pool.address, account0)

    tx = liquidity_pool.swapPutIn(
        [weth_address, dai_address], tx.return_value, {"from": account0}
    )
    tx.wait(1)

    print(
        "Tokens swapped into liquidity pool, checking account0 and liquidity pool balances"
    )
    get_balance(weth_address, account0)
    get_balance(dai_address, account0)
    print("----------")
    get_balance(weth_address, liquidity_pool.address)
    get_balance(dai_address, liquidity_pool.address)

    print(f"Current Exchange Rate DAI/ETH: {liquidity_pool.quote()}")

    # Account 0 wants their liquidity back and burns their tokens for the liquity back
    lp_token_amount = get_balance(lp_token_address, account0)
    approve_token(lp_token_address, lp_token_amount, liquidity_pool.address, account0)

    liquidity_pool.withdraw(lp_token_amount, {"from": account0})

    print("LP Tokens burned, checking account0 and liquidity pool balances")
    get_balance(weth_address, account0)
    get_balance(dai_address, account0)
    get_balance(lp_token_address, account0)
    print("----------")
    get_balance(weth_address, liquidity_pool.address)
    get_balance(dai_address, liquidity_pool.address)


# 0xE7eD6747FaC5360f88a2EFC03E00d25789F69291
if __name__ == "__main__":
    main()
