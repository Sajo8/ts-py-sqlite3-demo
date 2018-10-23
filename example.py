import os
from tswrapper import TRTLServices
import sqlite3
import json

# This example shows how to create new addresses
# scan them for incoming transactions by blockheight
# and store them into a sqlite3 database

#set token
os.environ["TRTL_SERVICES_TOKEN"] = "<TOKEN>"

#create sql db if not exist
conn = sqlite3.connect("./db.sqlite")

#open db connection
c = conn.cursor()

#create address tables if not exist
c.execute("""CREATE TABLE IF NOT EXISTS addresses (
            id integer PRIMARY KEY AUTOINCREMENT,
            address text NOT NULL,
            balance decimal(24, 2) DEFAULT 0.00,
            locked decimal(24, 2) DEFAULT 0.00,
            blockIndex integer NOT NULL,
            scanIndex integer NOT NULL,
            created integer DEFAULT CURRENT_TIMESTAMP
        );""")

#create transaction table if not exist
c.execute("""CREATE TABLE IF NOT EXISTS transactions (
            id integer PRIMARY KEY AUTOINCREMENT,
            address text NOT NULL,
            amount decimal(24, 2) DEFAULT 0.00,
            fee decimal(24, 2) DEFAULT 0.00,
            sfee decimal(24, 2) DEFAULT 0.00,
            blockIndex integer NOT NULL,
            transactionHash text NOT NULL,
            paymendId text NOT NULL,
            extra text NOT NULL,
            timestamp integer NOT NULL,
            confirms integer DEFAULT 0,
            created integer DEFAULT CURRENT_TIMESTAMP
        );""")

#create new address
new_address = TRTLServices.createAddress()

#prepare db insert
payload = ( new_address['address'], new_address['blockIndex'], new_address['blockIndex'])
c.execute('INSERT INTO addresses (address, blockIndex, scanIndex) VALUES (?,  ? , ?)', payload)
print('[' + new_address['address'] + '] stored in db.')


#select and loop through addresses stored in sqlite
for addresses in c.execute('SELECT * from addresses;'):

    address = addresses[1]
    blockIndex = addresses[4]
    scanIndex = addresses[5]
    newIndex = scanIndex + 100

    #check if addresses needs to be scanned
    getStatus = TRTLServices.getStatus()

    knownBlockCount = getStatus[1]['blockIndex']
    heightDiff = knownBlockCount - scanIndex

    if scanIndex >= knownBlockCount:
        print('Reached top of chain.')
        end()

    if heightDiff < 100:
        newIndex = knownBlockCount

    #scan each address for transactions
    incoming_txs = TRTLServices.scanAddress(address, int(scanIndex))

    if not incoming_txs:

        print('[' + address + '] no transactions found between height: ' + str(scanIndex) + ' - ' + str(newIndex))
    else:
        #loop through each found tx and insert it
        for tx in incoming_txs:
            
            print(tx)
            #store transactons, sfee = 0 for incoming
            payload = (address, int(tx.amount), int(tx.fee), tx.blockIndex, tx.transactionHash, tx.paymendId, tx.extra, tx.timestamp, tx.confirms)
            c.execute('INSERT INTO transactions (address, amount, fee, blockIndex, transactionHash, paymentId, extra, timestamp, confirms) VALUES (?,  ? , ?, ?, ?,  ? , ?, ?, ?)', payload)
            
            #update scanIndex of the scanned account.
            payload = (newIndex, address)
            c.execute('UPDATE addresses SET scanIndex = ? WHERE address = ?')

            conn.commit()
            print('[' + address + '] stored ' + len(incoming_txs) + ' transactions found between height: ' + str(scanIndex) + ' - ' + str(newIndex))


#load transactions
for txs in c.execute('SELECT * from transactions;'):
    print(txs)


#close connection
conn.close()
