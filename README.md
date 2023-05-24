# Intergration-with-AI-Agents

This project demonstrates the integration of Fetch.ai agents and the Peaq network on the Cosmos blockchain for balance maintenance between two cross-chain machine identities, Bob and Alice. The objective is to ensure that both identities always maintain a minimum balance of 5 tokens in their Peaq accounts.

### Project Overview

The project consists of two machine accounts, Bob and Alice, that interact with each other using Fetch.ai agents and the Peaq network. The objective is to ensure that both agents maintain a minimum balance of 5 tokens in their Peaq accounts.

To achieve this, the project utilizes a mapping stored in the Peaq network, which associates each machine identity's cross-chain address with its respective Fetch agent and wallet address. This mapping facilitates easy retrieval of communication details.

Periodically, both identities check their Peaq account balances. If the balance of either identity falls below 5 tokens, that identity sends a message to the other identity using the uagents package. The purpose of the message is to prompt the identity with the low balance to take action to restore their balance to at least 5 tokens.

To send the message, the sending identity needs to obtain the agent address of the recipient. This is achieved by retrieving the recipient's cross-chain address from the mapping stored in the Peaq network. Once the sender has the agent address, it sends the message to the recipient agent.

Upon receiving the message, the recipient identity retrieves the sender's cross-chain address from the mapping in the Peaq network. With this address, the recipient identity can send tokens to the sender's Peaq address, ensuring that the sender maintains a balance of at least 5 tokens.

## Installation

To run this project, you need Python 3.8, 3.9, or 3.10 on your system.

1. Clone the repository:

   ```shell
   git clone https://github.com/peaqnetwork/Intergration-with-AI-Agents.git

2. Create a Virtual Environment using Poetry by following the instructions [here](https://python-poetry.org/docs/#installation).

3. Open a terminal or command prompt and navigate to the project directory.

4. Create and enter a new Poetry virtual environment by running the following commands:

   ```shell
   poetry init -n
5. Once inside the virtual environment, run the following command to install the project dependencies:
   ```shell 
   python3 -m pip install -r requirements.txt

### Running the Agents

1. To run the agents open two terminal and create poetry virtual environment using this command: 
      ```shell
   poetry shell
2. Now you just need to run these files in those two terminal:  

Terminal 1

      poetry run python3 alice.py

Terminal 2

      poetry run python3 bob.py