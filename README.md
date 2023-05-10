# NFT Collection Analyzer

This repository contains a Python program for analyzing NFT (Non-Fungible Token) collections. The program connects to a SQLite database, retrieves data from the OpenSea API, and performs various analyses on the NFT collections.

## Installation

1. Clone the repository to your local machine.
2. Install the required dependencies by running the following command:

   ```shell
   pip install -r requirements.txt

   ```

3. Set up your environment variables by creating a .env file and adding the necessary variables:

   ```
   ALCHEMY_API_KEY=<your_alchemy_api_key>
   ```

   ## Usage

4. Modify the collections.txt file to include the URLs of the NFT collections you want to analyze, with each URL on a separate line.

5. Run the program using the following command:
   ```
   python main.py
   ```
6. Follow the prompts to provide the maximum and minimum floor prices for filtering the collections.

7. The program will analyze each collection, gather data from the OpenSea API, and store the results in the SQLite database (../db/db_collections.db).

## Results

The program generates a collection_analyzed.txt file that reflects the analysis results for each NFT collection in the collections.txt file. The lines in the file are annotated with various markers to indicate different conditions, such as floor price thresholds, safe percentages, and collection errors.

## Contributing

Contributions to the NFT Collection Analyzer project are welcome. If you encounter any issues or have suggestions for improvements, please create an issue or submit a pull request.
