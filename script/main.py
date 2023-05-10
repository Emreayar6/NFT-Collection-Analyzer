import sqlite3
import time
import requests
import json
import dotenv
import os

# Load .env variables
dotenv.load_dotenv()
ALCHEMY_API_KEY = os.environ.get('ALCHEMY_API_KEY')


def createTable(table_name):
    conn = sqlite3.connect('../db/db_collections.db')
    print("Database has been connected..")

    cursor = conn.cursor()
    cursor.execute(""" CREATE TABLE IF NOT EXISTS {} (
       time text,
       ratio real,
       safe_percentage real,
       numb_sales int,
       error real,
       buyers int,
       floor_price float
       )""".format(table_name))

    conn.commit()

    conn.close()


def addData(table_name, time, ratio, safe_Percentage, numb_sales, error, buyers, floor_price):

    createTable(table_name)
    conn = sqlite3.connect('../db/db_collections.db')
    print("Database has been connected..")

    cursor = conn.cursor()

    cursor.execute("""INSERT INTO {} VALUES {}""".format(
        table_name, (time, ratio, safe_Percentage, numb_sales, error, buyers, floor_price)))
    print("Data has been saved...")

    conn.commit()

    conn.close()


def readLastRow(table_name):
    createTable(table_name)
    conn = sqlite3.connect('../db/db_collections.db')
    print("Database has been connected..")

    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM {} ORDER BY strftime('%s', time) DESC LIMIT 1 OFFSET (SELECT COUNT(*) FROM {}) - 1".format(table_name, table_name))

    result = cursor.fetchone()

    print("Last row has been fetched...")

    conn.commit()

    conn.close()

    return result


def analyzeCollection(name):

    error = 0

    buyers = set()

    numb_sales = 0

    fee = 0

    floor_price = 0

    try:

        url = "https://api.opensea.io/api/v1/collection/{}".format(name)

        response = requests.get(url)

        df = response.json()

        address = df['collection']['primary_asset_contracts'][0]['address']

        fee_base = df['collection']['fees']

        floor_price = df['collection']['stats']['floor_price']
        try:
            if fee_base['seller_fees'] == {}:
                fee = fee_base['opensea_fees'][list(
                    fee_base['opensea_fees'].keys())[0]]
            else:
                fee = fee_base['opensea_fees'][list(fee_base['opensea_fees'].keys())[
                    0]] + fee_base['seller_fees'][list(fee_base['seller_fees'].keys())[0]]
        except:
            fee = fee_base['seller_fees'][list(
                fee_base['seller_fees'].keys())[0]]
        fee = fee / 100

        numb_sales = int(df['collection']['stats']['one_day_sales'])

    except:
        error = 1
        ratio = 1
        floor_price - 1

    if numb_sales > 0:

        try:
            url2 = "https://eth-mainnet.g.alchemy.com/nft/v2/{}/getNFTSales?fromBlock=0&toBlock=latest&order=desc&marketplace=seaport&contractAddress={}&limit={}".format(ALCHEMY_API_KEY,
                                                                                                                                                                          address, numb_sales)

            headers2 = {"accept": "application/json"}

            response2 = requests.get(url2, headers=headers2)

            df2 = response2.json()

            history = df2['nftSales']

            cost = df2['nftSales'][0]['sellerFee']['amount']
            cost = int(cost)
            cost = cost / 10**17

            amount_eth = 0
            amount_weth = 0

            for sale in history:
                buyers.add(sale['buyerAddress'])
                print(sale['buyerAddress'])
                if sale['protocolFee']['symbol'] == "ETH":
                    amount_eth += 1
                if sale['protocolFee']['symbol'] == "WETH":
                    amount_weth += 1

            ratio = amount_weth / (amount_eth + amount_weth)

        except:
            print("Error has been occured... ratio assigned as 1")
            ratio = 1
            error = 1

    else:
        print("No sales... ratio assigned as 1")
        ratio = 1

    if fee > 10:
        safe_Percentage = "*0.80*"
    else:
        safe_Percentage = ""

    return ratio, safe_Percentage, numb_sales, error, len(buyers), floor_price


with open("../collections/collections.txt", "r+") as file:

    list_of_lines = []
    xx = 0
    safePercentage = ""

    list_of_lines = file.readlines()

    max_floor_price = float(input("What is the MAX floor price? (0.089) "))
    min_floor_price = float(input("What is the MIN floor price? (0.089) "))

    for url in list_of_lines:

        print(str(xx+1) + "/" + str(len(list_of_lines)))

        is_safePercentage_set = False

        if url[0] == "-" and "*" in url:
            target_url = url[url.find('https'):url.find("*")]
            is_safePercentage_set = True
        elif url[0] == '-':
            target_url = url[url.find('https'):]
        elif "*" in url:
            target_url = url[:url.find("*")]
            is_safePercentage_set = True
        else:
            target_url = url

        name = target_url[target_url.find('collection/')+11:]
        name = name.replace("\n", "")
        print(name)

        ratio, safePercentage, numbSales, p_error, buyers, floor_price = analyzeCollection(
            name)
        change_floor_price = 0
        isNew = False
        table_name = "tb_" + name.replace("-", "_")
        try:
            previous_floor_price = readLastRow(table_name)[6]
            print("Previous Floor Price ---> ", previous_floor_price)
            isNew = False
        except:
            print("New Collection")
            isNew = True

        if not p_error == 1:
            addData(table_name, time.ctime(), ratio, safePercentage,
                    numbSales, p_error, buyers, floor_price)
        else:
            if "\n" in list_of_lines[xx]:
                list_of_lines[xx] = "- KONTROL ET -" + list_of_lines[xx]
            else:
                list_of_lines[xx] = "- KONTROL ET -" + list_of_lines[xx] + "\n"

            xx += 1

            file_w = open("../collections/collection_analyzed.txt", "w")
            file_w.writelines(list_of_lines)
            file_w.close()
            continue

        len_buyers = buyers
        if isNew:
            change_floor_price = 0
        else:
            change_floor_price = abs(
                (floor_price - previous_floor_price) / previous_floor_price)
            print("Change of floor price ---> ", change_floor_price)

        if min_floor_price > floor_price:
            if "\n" in list_of_lines[xx]:
                list_of_lines[xx] = "- HEDEF FLOOR ALTINDA -" + \
                    list_of_lines[xx]
            else:
                list_of_lines[xx] = "- HEDEF FLOOR ALTINDA -" + \
                    list_of_lines[xx] + "\n"

            xx += 1
            print("--- HEDEF FLOOR ALTINDA ---")

            file_w = open("../collections/collection_analyzed.txt", "w")
            file_w.writelines(list_of_lines)
            file_w.close()
            continue

        if max_floor_price < floor_price:
            if "\n" in list_of_lines[xx]:
                list_of_lines[xx] = "- HEDEF FLOOR USTUNDE -" + \
                    list_of_lines[xx]
            else:
                list_of_lines[xx] = "- HEDEF FLOOR USTUNDE -" + \
                    list_of_lines[xx] + "\n"

            xx += 1
            print("--- HEDEF FLOOR USTUNDE ---")

            file_w = open("../collections/collection_analyzed.txt", "w")
            file_w.writelines(list_of_lines)
            file_w.close()
            continue

        if change_floor_price > 0.5:
            if "\n" in list_of_lines[xx]:
                list_of_lines[xx] = "- ANI FLOOR DEGISIMI -" + \
                    list_of_lines[xx]
            else:
                list_of_lines[xx] = "- ANI FLOOR DEGISIMI -" + \
                    list_of_lines[xx] + "\n"

            xx += 1
            print("--- ANI FLOOR DEGISIMI ---")

            file_w = open("../collections/collection_analyzed.txt", "w")
            file_w.writelines(list_of_lines)
            file_w.close()
            continue

        if not is_safePercentage_set:
            if (ratio > 0.7) or (numbSales < 5) or (len_buyers < 3) or (change_floor_price > 0.7):
                if "\n" in list_of_lines[xx]:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx] = list_of_lines[xx][:-
                                                              1] + safePercentage + "\n"
                    else:
                        list_of_lines[xx] = "-" + \
                            list_of_lines[xx][:-1] + safePercentage + "\n"
                else:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx] = list_of_lines[xx] + safePercentage
                    else:
                        list_of_lines[xx] = "-" + \
                            list_of_lines[xx] + safePercentage
            else:
                if "\n" in list_of_lines[xx]:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx] = list_of_lines[xx][1:-
                                                              1] + safePercentage + "\n"
                    else:
                        list_of_lines[xx] = list_of_lines[xx][:-
                                                              1] + safePercentage + "\n"
                else:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx] = list_of_lines[xx][1:] + \
                            safePercentage
                    else:
                        list_of_lines[xx] = list_of_lines[xx] + safePercentage
        else:
            if (ratio > 0.7) or (numbSales < 5) or (len_buyers < 3) or (change_floor_price > 0.7):
                if "\n" in list_of_lines[xx]:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx] = list_of_lines[xx][:-1] + "\n"
                    else:
                        list_of_lines[xx] = "-" + list_of_lines[xx][:-1] + "\n"
                else:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx] = list_of_lines[xx][1:]
                    else:
                        list_of_lines[xx] = "-" + list_of_lines[xx]
            else:
                if "\n" in list_of_lines[xx]:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx] = list_of_lines[xx][1:-1] + "\n"
                    else:
                        list_of_lines[xx] = list_of_lines[xx][:-1] + "\n"
                else:
                    if list_of_lines[xx][0] == "-":
                        list_of_lines[xx][1:] = list_of_lines[xx]
                    else:
                        list_of_lines[xx] = list_of_lines[xx]

        xx += 1

        file_w = open("../collections/collection_analyzed.txt", "w")
        file_w.writelines(list_of_lines)
        file_w.close()
