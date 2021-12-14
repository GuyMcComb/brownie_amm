from brownie import accounts, config, interface, network
from web3 import Web3

weth_amount = Web3.toWei(0.1, "ether")

# GOING TO INTERACT WITH 3 ACCOUNTS
# ACCOUNT 1 IS GOING TO HOLD 100 ETH AND APPROVE ACCOUNT 2 TO SEND 10 ETH
# ACCOUNT 3 WILL RECEIVE THE 10 ETH SENT FROM ACCOUNT 1, BUT SENT BY ACCOUNT 2


def get_weth(account=None):
    """
    Mints WETH by depositing ETH.
    """
    account = (
        account if account else accounts.add(config["wallets"]["from_key"])
    )  # add your keystore ID as an argument to this call
    weth = interface.WethInterface(
        config["networks"][network.show_active()]["weth_token"]
    )
    tx = weth.deposit({"from": account, "value": weth_amount})
    print("Received 1 WETH")
    return tx


def erc20_approve(sender, account_holder, token_address):
    tx = token_address.approve(sender, weth_amount, {"from": account_holder})
    print(f"Approved account {sender} to send Weth from {account_holder}")
    return tx


def erc20_transfer_from(account_0, account_1, account_2, weth):
    print("Calling Transfer From")
    tx = weth.transferFrom(account_0, account_1, weth_amount, {"from": account_2})
    print("Weth transferred")


def print_erc20_balance(account, weth):
    print(weth.balanceOf(account), f"WETH balance {account}")


def main():

    account_0 = get_account()
    account_1 = get_accounts(index=1)
    account_2 = get_accounts(index=2)

    weth_address = interface.WethInterface(
        config["networks"][network.show_active()]["weth_token"]
    )

    for acc in [account_0, account_1, account_2]:
        get_weth(account=acc)
        print_erc20_balance(acc, weth_address)

    approve_weth(account_0, account_2, weth_address)
    transfer_weth_from(account_0, account_1, account_2, weth_address)

    for acc in [account_0, account_1, account_2]:
        print_erc20_balance(acc, weth_address)

    # approve_erc20(amount, lending_pool.address, weth_address, account_0)
    # print("Depositing...")
    # lending_pool.deposit(weth_address, amount, account_0.address, 0, {"from": account_0})
    # print("Deposited!")
    # borrowable_eth, total_debt_eth = get_borrowable_data(lending_pool, account_0)
    # print(f"LETS BORROW IT ALL")
    # erc20_eth_price = get_asset_price()
    # amount_erc20_to_borrow = (1 / erc20_eth_price) * (borrowable_eth * 0.95)
    # print(f"We are going to borrow {amount_erc20_to_borrow} DAI")
    # borrow_erc20(lending_pool, amount_erc20_to_borrow, account_0)

    # borrowable_eth, total_debt_eth = get_borrowable_data(lending_pool, account_0)
    ## amount_erc20_to_repay = (1 / erc20_eth_price) * (total_debt_eth * 0.95)
    # repay_all(amount_erc20_to_borrow, lending_pool, account_0)


def get_account():
    if network.show_active() in ["hardhat", "development", "mainnet-fork"]:
        return accounts[0]
    if network.show_active() in config["networks"]:
        account = accounts.add(config["wallets"]["from_key"])
        return account
    return None


def get_accounts(index: int):
    if network.show_active() in ["hardhat", "development", "mainnet-fork"]:
        return accounts[index]
    if network.show_active() in config["networks"]:
        account = accounts.add(config["wallets"]["from_key"])
        return account
    return None


# def get_lending_pool():
#    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
#        config["networks"][network.show_active()]["lending_pool_addresses_provider"]
#    )
#    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
#    lending_pool = interface.ILendingPool(lending_pool_address)
#    return lending_pool


# def approve_erc20(amount, lending_pool_address, erc20_address, account):
#    print("Approving ERC20...")
#    erc20 = interface.IERC20(erc20_address)
#    tx_hash = erc20.approve(lending_pool_address, amount, {"from": account})
#    tx_hash.wait(1)
#    print("Approved!")
#    return True


# def get_borrowable_data(lending_pool, account):
#    (
#        total_collateral_eth,
#        total_debt_eth,
#        available_borrow_eth,
#        current_liquidation_threshold,
#        tlv,
#        health_factor,
#    ) = lending_pool.getUserAccountData(account.address)
#    available_borrow_eth = Web3.fromWei(available_borrow_eth, "ether")
#    total_collateral_eth = Web3.fromWei(total_collateral_eth, "ether")
#    total_debt_eth = Web3.fromWei(total_debt_eth, "ether")
#    print(f"You have {total_collateral_eth} worth of ETH deposited.")
#    print(f"You have {total_debt_eth} worth of ETH borrowed.")
#    print(f"You can borrow {available_borrow_eth} worth of ETH.")
#    return (float(available_borrow_eth), float(total_debt_eth))


# def borrow_erc20(lending_pool, amount, account, erc20_address=None):
#    erc20_address = (
#        erc20_address
#        if erc20_address
#        else config["networks"][network.show_active()]["aave_dai_token"]
#    )
#    # 1 is stable interest rate
#    # 0 is the referral code
#    transaction = lending_pool.borrow(
#        erc20_address,
#        Web3.toWei(amount, "ether"),
#        1,
#        0,
#        account.address,
#        {"from": account},
#    )
#    transaction.wait(1)
#    print(f"Congratulations! We have just borrowed {amount}")


# def get_asset_price():
#    # For mainnet we can just do:
#    # return Contract(f"{pair}.data.eth").latestAnswer() / 1e8
#    dai_eth_price_feed = interface.AggregatorV3Interface(
#        config["networks"][network.show_active()]["dai_eth_price_feed"]
#    )
#    latest_price = Web3.fromWei(dai_eth_price_feed.latestRoundData()[1], "ether")
#    print(f"The DAI/ETH price is {latest_price}")
#    return float(latest_price)


# def repay_all(amount, lending_pool, account):
#    approve_erc20(
#        Web3.toWei(amount, "ether"),
#        lending_pool,
#        config["networks"][network.show_active()]["aave_dai_token"],
#        account,
#    )
#    tx = lending_pool.repay(
#        config["networks"][network.show_active()]["aave_dai_token"],
#        Web3.toWei(amount, "ether"),
#        1,
#        account.address,
#        {"from": account},
#    )
#    tx.wait(1)
#    print("Repaid!")


if __name__ == "__main__":
    main()
