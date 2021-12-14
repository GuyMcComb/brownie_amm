pragma solidity ^0.8.0;
// SPDX-License-Identifier: MIT
// This is a basic liquidity pool contract. It is used for prototyping an automated market maker.
// Second step will be a factory contract that deploys this contract for multiple token pairs.
// Improvements to be made:
//      - Add modifiers
//      - Add indexing to events

import "./ERC20PresetMinterPauser.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";
import "./ABDKMathQuad.sol";

contract LiquidityPool {

    using SafeMath for uint256;

    mapping(address => uint256) public reserves;

    mapping(address => IERC20) public interfaces;

    address public token0;
    address public token1;

    address public lpTokenAddress;
    uint256 public lpTokenTotalSupply;

    uint256 internal transactionFee = 5;

    ERC20PresetMinterPauser public lpToken;

    event LpCreated(address[2] tokens);
    event LpTokenCreated(string name, string ticker, address tokenAddress);

    event DepositConfirmed(
        address[2] tokens,
        uint256[2] tokenAmounts,
        uint256[2] tokenReserves,
        uint256 lpTokensCreated
    );
    event WithdrawalConfirmed(
        address[2] tokens,
        uint256[2] tokenAmounts,
        uint256[2] tokenReserves,
        uint256 lpTokensBurned
    );

    constructor(address[2] memory tokens, string memory lpTokenName, string memory lpTokenTicker) public {
        (token0, token1) = sortTokens(tokens[0], tokens[1]);

        interfaces[token0] = IERC20(token0);
        interfaces[token1] = IERC20(token1);

       lpTokenAddress = address(
            new ERC20PresetMinterPauser(lpTokenName, lpTokenTicker)
        );

        lpToken = ERC20PresetMinterPauser(lpTokenAddress);

        emit LpTokenCreated(lpTokenName, lpTokenTicker, lpTokenAddress);

        lpTokenTotalSupply = 1000;

        emit LpCreated(tokens);
    }

    // This function could be deleted and front end can read from logs
    function returnTokenAddress() public view returns (address) {
        return lpTokenAddress;
    }

    function quote() public view returns (uint256) {
        uint256 exchangeRate = reserves[token1].div(reserves[token0]);
        return exchangeRate;
    }

    function sortTokens(address tokenA,  address tokenB) internal pure returns(address, address){
        address tokenHigh;
        address tokenLow;

        if (tokenA > tokenB){
            (tokenHigh, tokenLow) = (tokenA, tokenB);
            }
        else{
            (tokenHigh, tokenLow) = (tokenB, tokenA);
            }

        return (tokenHigh, tokenLow);
    }

    function sortTokensAndAmounts(address tokenA, uint256 tokenAAmount, address tokenB, uint256 tokenBAmount) internal pure returns(address, uint256, address, uint256){
        address tokenHigh;
        uint256 tokenHighAmount;
        address tokenLow;
        uint256 tokenLowAmount;

        if (tokenA > tokenB){
            (tokenHigh, tokenHighAmount, tokenLow, tokenLowAmount) = (tokenA, tokenAAmount, tokenB, tokenBAmount);
            }
        else{
            (tokenHigh, tokenHighAmount, tokenLow, tokenLowAmount) = (tokenB, tokenBAmount, tokenA, tokenAAmount);
            }

        return (tokenHigh, tokenHighAmount, tokenLow, tokenLowAmount);
    }


    function calculatePercentage(uint x, uint y, uint z)
        public pure returns (uint) {
        // y * 100 / x - how much is y a percentage of x
        // x * y / 100 - x percent of y
            return
            ABDKMathQuad.toUInt (
              ABDKMathQuad.div (
                ABDKMathQuad.mul (
                  ABDKMathQuad.fromUInt(x),
                  ABDKMathQuad.fromUInt(y)
                ),
                ABDKMathQuad.fromUInt(z)
              )
            );
        }


    function deposit(address[] memory tokens, uint256[] memory tokenAmounts) public {
        uint256 token0Amount;
        uint256 token1Amount;

        (token0, token0Amount, token1, token1Amount) = sortTokensAndAmounts(tokens[0], tokenAmounts[0], tokens[1], tokenAmounts[1]);

        interfaces[token0].transferFrom(msg.sender, address(this), token0Amount);
        interfaces[token1].transferFrom(msg.sender, address(this), token1Amount);

        reserves[token0] = reserves[token0].add(token0Amount);
        reserves[token1] = reserves[token1].add(token1Amount);

        uint256 lpTokenAmount = token0Amount;

        lpToken.mint(msg.sender, lpTokenAmount);
        lpTokenTotalSupply = lpTokenTotalSupply.add(lpTokenAmount);

        emit DepositConfirmed(
            [token0, token1],
            [token0Amount, token1Amount],
            [reserves[token0], reserves[token1]],
            lpTokenAmount
        );
    }


    function withdraw(uint256 lpTokenAmount) public {
        //y * 100 / x - what percentage is y of x

        uint256 lpTokenPer = calculatePercentage(lpTokenAmount, 100, lpTokenTotalSupply);

        // x * y / 100 - how much is x percent of y
        uint256 token0Amount = calculatePercentage(lpTokenPer, reserves[token0], 100);
        uint256 token1Amount = calculatePercentage(lpTokenPer, reserves[token1], 100);

        lpToken.burnFrom(msg.sender, lpTokenAmount);
        lpTokenTotalSupply = lpTokenTotalSupply.sub(lpTokenAmount);

        reserves[token0] = reserves[token0].sub(token0Amount);
        reserves[token1] = reserves[token1].sub(token1Amount);

        interfaces[token0].transfer(msg.sender, reserves[token0]);
        interfaces[token1].transfer(msg.sender, reserves[token1]);

        emit WithdrawalConfirmed(
            [token0, token1],
            [token0Amount, token1Amount],
            [reserves[token0], reserves[token1]],
            lpTokenAmount
        );
    }


    function calculateTokensOut(address[] memory tokens, uint256 tokenAmount) public view returns(uint256){
        // (x + x1_in) * (y - y1_out) = k;
        // y1_out = y-(k/(x + x1_in));
        // Putting a 5% transaction fee
        uint256 k = reserves[tokens[0]].mul(reserves[tokens[1]]);
        uint256 x1 = calculatePercentage(100 - transactionFee, tokenAmount, 100);
        uint256 x = reserves[tokens[0]];
        uint256 y = reserves[tokens[1]];
        uint256 y1 = y.sub(k.div(x.add(x1)));

    return y1;

}


    function swapPutIn(address[] memory tokens, uint256 tokenAmountIn)
        public
        returns (uint256)
    {
        uint256 tokenAmountOut = calculateTokensOut(tokens, tokenAmountIn);

        reserves[tokens[0]] = reserves[tokens[0]].add(tokenAmountIn);
        reserves[tokens[1]] = reserves[tokens[1]].sub(tokenAmountOut);

        interfaces[tokens[0]].transferFrom(msg.sender, address(this), tokenAmountIn);
        interfaces[tokens[1]].transfer(msg.sender, tokenAmountOut);
    return tokenAmountOut;

        }

}
