# Intergration-with-AI-Agents

This project demonstrates the integration of Fetch.ai agents and the Peaq network on the Cosmos blockchain for balance maintenance between two cross-chain machine identities, Bob and Alice. The objective is to ensure that both identities always maintain a minimum balance of 5 tokens in their Peaq accounts.

To achieve this, the project utilizes a mapping stored in the Peaq network, which associates each machine identity's cross-chain address with its respective Fetch agent and wallet address. This mapping facilitates easy retrieval of communication details.

Periodically, both identities check their Peaq account balances. If the balance of either identity falls below 5 tokens, that identity sends a message to the other identity using the uagents package. The purpose of the message is to prompt the identity with the low balance to take action to restore their balance to at least 5 tokens.

To send the message, the sending identity needs to obtain the agent address of the recipient. This is achieved by retrieving the recipient's cross-chain address from the mapping stored in the Peaq network. Once the sender has the agent address, it sends the message to the recipient agent.

Upon receiving the message, the recipient identity retrieves the sender's cross-chain address from the mapping in the Peaq network. With this address, the recipient identity can send tokens to the sender's Peaq address, ensuring that the sender maintains a balance of at least 5 tokens.
